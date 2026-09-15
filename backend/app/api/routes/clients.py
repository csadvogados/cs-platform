import csv
import io
import re
import unicodedata
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.client import Client
from app.models.crm import CRMContact, CRMInteraction, CRMOpportunity, CRMTask, CommercialContract, Lead, LeadInteraction, LeadTask, LeadSource, ServiceType
from app.models.document import ClientDocument
from app.models.financial import Debt, Diagnosis, Expense, Income, PaymentAgreement
from app.models.negotiation import Negotiation
from app.models.recovery import RecoveryCase
from app.models.user import User
from app.schemas.client import (
    ClientCreate,
    ClientImportPreview,
    ClientImportPreviewRow,
    ClientImportRequest,
    ClientImportResult,
    ClientPage,
    ClientProfileItem,
    ClientProfileSummary,
    ClientRead,
    ClientUpdate,
)
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode
from app.services.audit import record_audit

router = APIRouter()


CLIENT_STATUS_LABELS = {
    "lead": "Potencial cliente",
    "triage": "Triagem",
    "proposal": "Proposta",
    "contracted": "Contratado",
    "documents_pending": "Documentos pendentes",
    "diagnosis": "Diagnóstico",
    "negotiation": "Negociação",
    "judicial_review": "Análise judicial",
    "judicial": "Judicial",
    "agreement": "Acordo",
    "closed": "Encerrado",
    "cancelled": "Cancelado",
}

MAX_IMPORT_BYTES = 2 * 1024 * 1024
MAX_IMPORT_ROWS = 500
IMPORT_HEADER_ALIASES = {
    "nome": "full_name",
    "nome_completo": "full_name",
    "full_name": "full_name",
    "cpf": "cpf",
    "rg": "rg",
    "nascimento": "birth_date",
    "data_de_nascimento": "birth_date",
    "birth_date": "birth_date",
    "profissao": "profession",
    "profession": "profession",
    "e_mail": "email",
    "email": "email",
    "telefone": "phone",
    "celular": "phone",
    "phone": "phone",
    "cidade": "city",
    "city": "city",
    "estado": "state",
    "uf": "state",
    "state": "state",
    "status": "status",
    "pessoa_natural": "person_natural",
    "boa_fe": "good_faith_declared",
    "boa_fe_declarada": "good_faith_declared",
    "good_faith_declared": "good_faith_declared",
    "capacidade_de_pagamento": "can_pay_without_harming_basics",
    "can_pay_without_harming_basics": "can_pay_without_harming_basics",
    "observacao": "notes",
    "observacoes": "notes",
    "notes": "notes",
}
IMPORT_FIELD_LABELS = {
    "full_name": "Nome",
    "cpf": "CPF",
    "rg": "RG",
    "birth_date": "Nascimento",
    "profession": "Profissão",
    "email": "E-mail",
    "phone": "Telefone",
    "city": "Cidade",
    "state": "Estado",
    "status": "Status",
    "person_natural": "Pessoa natural",
    "good_faith_declared": "Boa-fé declarada",
    "can_pay_without_harming_basics": "Capacidade de pagamento",
    "notes": "Observações",
}


def _normalize_import_key(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = "".join(character for character in normalized if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "_", ascii_value.lower()).strip("_")


CLIENT_STATUS_IMPORT_VALUES = {
    _normalize_import_key(label): value for value, label in CLIENT_STATUS_LABELS.items()
}
CLIENT_STATUS_IMPORT_VALUES.update(
    {_normalize_import_key(value): value for value in CLIENT_STATUS_LABELS}
)


def _safe_import_filename(value: str | None) -> str:
    filename = re.split(r"[\\/]", str(value or "clientes.csv"))[-1].strip()
    return (filename or "clientes.csv")[:255]


def _import_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _parse_import_date(value: object) -> date | None:
    text = _import_text(value)
    if not text:
        return None
    for pattern in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    raise ValueError("Nascimento deve usar o formato DD/MM/AAAA.")


def _parse_import_boolean(value: object, *, default: bool | None) -> bool | None:
    text = _normalize_import_key(value)
    if not text or text in {"nao_informado", "nao_informada"}:
        return default
    if text in {"sim", "s", "yes", "true", "1"}:
        return True
    if text in {"nao", "n", "no", "false", "0"}:
        return False
    raise ValueError("Use Sim ou Não nos campos de confirmação.")


def _parse_import_status(value: object) -> str:
    text = _normalize_import_key(value)
    if not text:
        return "lead"
    status_value = CLIENT_STATUS_IMPORT_VALUES.get(text)
    if not status_value:
        raise ValueError("Status não reconhecido.")
    return status_value


def _import_validation_errors(exc: ValidationError) -> list[str]:
    errors = []
    for error in exc.errors():
        field = str(error.get("loc", ("registro",))[0])
        label = IMPORT_FIELD_LABELS.get(field, field)
        if field == "cpf":
            message = "deve conter 11 dígitos e não pode ter todos os números iguais."
        elif field == "email":
            message = "endereço inválido."
        elif field == "full_name":
            message = "informe pelo menos 3 caracteres."
        elif field == "state":
            message = "informe uma UF com 2 letras."
        else:
            message = "valor inválido."
        errors.append(f"{label}: {message}")
    return errors


def _build_import_client(row: dict[str, object], header_map: dict[str, str]) -> ClientCreate:
    values = {
        target: row.get(source)
        for source, target in header_map.items()
        if source is not None
    }
    payload = {
        "full_name": _import_text(values.get("full_name")),
        "cpf": _import_text(values.get("cpf")),
        "rg": _import_text(values.get("rg")),
        "birth_date": _parse_import_date(values.get("birth_date")),
        "profession": _import_text(values.get("profession")),
        "email": _import_text(values.get("email")),
        "phone": _import_text(values.get("phone")),
        "city": _import_text(values.get("city")),
        "state": _import_text(values.get("state")),
        "status": _parse_import_status(values.get("status")),
        "person_natural": _parse_import_boolean(values.get("person_natural"), default=True),
        "good_faith_declared": _parse_import_boolean(values.get("good_faith_declared"), default=None),
        "can_pay_without_harming_basics": _parse_import_boolean(
            values.get("can_pay_without_harming_basics"),
            default=None,
        ),
        "notes": _import_text(values.get("notes")),
    }
    return ClientCreate.model_validate(payload)


def _decode_import_file(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            text = content.decode(encoding)
            if "\x00" in text:
                raise UnicodeDecodeError(encoding, content, 0, 1, "NUL")
            return text
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=400, detail="Não foi possível ler o CSV. Salve-o em UTF-8.")


def _read_import_rows(content: bytes) -> list[dict[str, object]]:
    text = _decode_import_file(content)
    first_line = text.splitlines()[0] if text.splitlines() else ""
    delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","
    try:
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="O CSV não possui cabeçalho.")

        header_map: dict[str, str] = {}
        mapped_fields: set[str] = set()
        for source in reader.fieldnames:
            target = IMPORT_HEADER_ALIASES.get(_normalize_import_key(source))
            if target and target not in mapped_fields:
                header_map[source] = target
                mapped_fields.add(target)

        missing = {"full_name", "cpf"} - mapped_fields
        if missing:
            raise HTTPException(status_code=400, detail="O CSV precisa conter as colunas Nome e CPF.")

        parsed_rows: list[dict[str, object]] = []
        for row in reader:
            if not any(_import_text(value) for value in row.values() if value is not None):
                continue
            if len(parsed_rows) >= MAX_IMPORT_ROWS:
                raise HTTPException(status_code=400, detail=f"O limite é de {MAX_IMPORT_ROWS} clientes por arquivo.")
            display_values = {
                target: row.get(source)
                for source, target in header_map.items()
                if source is not None
            }
            try:
                client = _build_import_client(row, header_map)
                parsed_rows.append({
                    "line": reader.line_num,
                    "client": client,
                    "errors": [],
                    "display_name": _import_text(display_values.get("full_name")),
                    "display_cpf": _import_text(display_values.get("cpf")),
                })
            except ValidationError as exc:
                parsed_rows.append({
                    "line": reader.line_num,
                    "client": None,
                    "errors": _import_validation_errors(exc),
                    "display_name": _import_text(display_values.get("full_name")),
                    "display_cpf": _import_text(display_values.get("cpf")),
                })
            except ValueError as exc:
                parsed_rows.append({
                    "line": reader.line_num,
                    "client": None,
                    "errors": [str(exc)],
                    "display_name": _import_text(display_values.get("full_name")),
                    "display_cpf": _import_text(display_values.get("cpf")),
                })
    except csv.Error as exc:
        raise HTTPException(status_code=400, detail="O arquivo CSV está malformado.") from exc

    if not parsed_rows:
        raise HTTPException(status_code=400, detail="O CSV não possui clientes para importar.")
    return parsed_rows


def _client_query(
    organization_id: uuid.UUID,
    query: str | None,
    client_status: str | None,
    include_archived: bool = False,
    archived_only: bool = False,
):
    stmt = select(Client).where(Client.organization_id == organization_id)
    if archived_only:
        stmt = stmt.where(Client.archived_at.is_not(None))
    elif not include_archived:
        stmt = stmt.where(Client.archived_at.is_(None))
    if query and query.strip():
        term = f"%{query.strip()}%"
        stmt = stmt.where(
            or_(
                Client.full_name.ilike(term),
                Client.cpf.ilike(term),
                Client.phone.ilike(term),
                Client.city.ilike(term),
                Client.email.ilike(term),
            )
        )
    if client_status:
        stmt = stmt.where(Client.status == client_status)
    return stmt


def _format_cpf(value: str | None) -> str:
    digits = "".join(character for character in str(value or "") if character.isdigit())
    if len(digits) != 11:
        return str(value or "")
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _csv_safe(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, datetime):
        text = value.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M")
    elif isinstance(value, date):
        text = value.strftime("%d/%m/%Y")
    else:
        text = str(value)

    normalized = text.lstrip()
    if normalized.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{text}"
    return text


def _boolean_label(value: bool | None) -> str:
    if value is None:
        return "Não informado"
    return "Sim" if value else "Não"


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    actor: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_CREATE.value)
    ),
):
    client = Client(organization_id=actor.organization_id, **payload.model_dump(mode="json"))
    db.add(client)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="CPF já cadastrado nesta organização") from exc
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.user_id,
        entity_type="client",
        entity_id=client.id,
        action="create",
        new_values={"full_name": client.full_name, "cpf": client.cpf, "status": client.status},
    )
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=list[ClientRead])
def list_clients(
    q: str | None = Query(default=None, max_length=200),
    client_status: str | None = Query(default=None, alias="status", max_length=40),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    include_archived: bool = Query(False),
    archived_only: bool = Query(False),
    db: Session = Depends(get_db),
    actor: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_READ.value)
    ),
):
    stmt = (
        _client_query(actor.organization_id, q, client_status, include_archived, archived_only)
        .order_by(Client.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


@router.get("/page", response_model=ClientPage)
def paginate_clients(
    q: str | None = Query(default=None, max_length=200),
    client_status: str | None = Query(default=None, alias="status", max_length=40),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=10, le=100),
    include_archived: bool = Query(False),
    archived_only: bool = Query(False),
    db: Session = Depends(get_db),
    actor: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_READ.value)
    ),
):
    filtered = _client_query(
        actor.organization_id, q, client_status, include_archived, archived_only
    )
    total = int(db.scalar(select(func.count()).select_from(filtered.subquery())) or 0)
    pages = (total + page_size - 1) // page_size if total else 0
    effective_page = min(page, pages) if pages else 1
    offset = (effective_page - 1) * page_size
    items = list(
        db.scalars(
            filtered
            .order_by(Client.created_at.desc(), Client.id.desc())
            .limit(page_size)
            .offset(offset)
        )
    )
    return ClientPage(
        items=items,
        total=total,
        page=effective_page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/export.csv")
def export_clients_csv(
    q: str | None = Query(default=None, max_length=200),
    client_status: str | None = Query(default=None, alias="status", max_length=40),
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions(PermissionCode.CLIENT_EXPORT.value)),
):
    stmt = _client_query(identity.organization_id, q, client_status).order_by(
        Client.full_name.asc(),
        Client.id.asc(),
    )
    clients = list(db.scalars(stmt))

    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(
        [
            "Nome",
            "CPF",
            "RG",
            "Nascimento",
            "Profissão",
            "E-mail",
            "Telefone",
            "Cidade",
            "Estado",
            "Status",
            "Pessoa natural",
            "Boa-fé declarada",
            "Capacidade de pagamento",
            "Observações",
            "Data de cadastro",
            "Última atualização",
        ]
    )
    for client in clients:
        writer.writerow(
            [
                _csv_safe(client.full_name),
                _csv_safe(_format_cpf(client.cpf)),
                _csv_safe(client.rg),
                _csv_safe(client.birth_date),
                _csv_safe(client.profession),
                _csv_safe(client.email),
                _csv_safe(client.phone),
                _csv_safe(client.city),
                _csv_safe(client.state),
                _csv_safe(CLIENT_STATUS_LABELS.get(client.status, client.status)),
                _csv_safe(client.person_natural),
                _csv_safe(_boolean_label(client.good_faith_declared)),
                _csv_safe(_boolean_label(client.can_pay_without_harming_basics)),
                _csv_safe(client.notes),
                _csv_safe(client.created_at),
                _csv_safe(client.updated_at),
            ]
        )

    record_audit(
        db,
        organization_id=identity.organization_id,
        user_id=identity.user_id,
        entity_type="client",
        entity_id=None,
        action="export",
        new_values={
            "count": len(clients),
            "query": q.strip() if q and q.strip() else None,
            "status": client_status,
        },
    )
    db.commit()

    filename = f"clientes_{datetime.now(timezone.utc):%Y-%m-%d}.csv"
    content = ("\ufeff" + stream.getvalue()).encode("utf-8")
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/import/template.csv")
def download_clients_import_template(
    _identity: IdentityContext = Depends(
        require_permissions(
            PermissionCode.CLIENT_CREATE.value,
            PermissionCode.CLIENT_EXPORT.value,
        )
    ),
):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(
        [
            "Nome",
            "CPF",
            "RG",
            "Nascimento",
            "Profissão",
            "E-mail",
            "Telefone",
            "Cidade",
            "Estado",
            "Status",
            "Pessoa natural",
            "Boa-fé declarada",
            "Capacidade de pagamento",
            "Observações",
        ]
    )
    content = ("\ufeff" + stream.getvalue()).encode("utf-8")
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="modelo_importacao_clientes.csv"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/import/preview", response_model=ClientImportPreview)
async def preview_clients_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(
        require_permissions(
            PermissionCode.CLIENT_CREATE.value,
            PermissionCode.CLIENT_EXPORT.value,
        )
    ),
):
    filename = _safe_import_filename(file.filename)
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Selecione um arquivo com extensão .csv.")

    content = await file.read(MAX_IMPORT_BYTES + 1)
    await file.close()
    if not content:
        raise HTTPException(status_code=400, detail="O arquivo CSV está vazio.")
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=400, detail="O CSV deve ter no máximo 2 MB.")

    parsed_rows = _read_import_rows(content)
    candidate_cpfs = {
        item["client"].cpf
        for item in parsed_rows
        if isinstance(item.get("client"), ClientCreate)
    }
    existing_cpfs = set()
    if candidate_cpfs:
        existing_cpfs = set(
            db.scalars(
                select(Client.cpf).where(
                    Client.organization_id == identity.organization_id,
                    Client.cpf.in_(candidate_cpfs),
                )
            )
        )

    rows: list[ClientImportPreviewRow] = []
    seen_cpfs: set[str] = set()
    duplicate_rows = 0
    for item in parsed_rows:
        client = item.get("client")
        errors = list(item.get("errors") or [])
        duplicate = False
        if isinstance(client, ClientCreate):
            if client.cpf in existing_cpfs:
                errors.append("CPF já cadastrado nesta organização.")
                duplicate = True
            elif client.cpf in seen_cpfs:
                errors.append("CPF repetido no próprio arquivo.")
                duplicate = True
            seen_cpfs.add(client.cpf)
        if duplicate:
            duplicate_rows += 1
        rows.append(
            ClientImportPreviewRow(
                line=int(item["line"]),
                valid=not errors,
                duplicate=duplicate,
                display_name=str(item.get("display_name") or "") or None,
                display_cpf=str(item.get("display_cpf") or "") or None,
                data=client if not errors else None,
                errors=errors,
            )
        )

    valid_rows = sum(1 for row in rows if row.valid)
    return ClientImportPreview(
        filename=filename,
        total_rows=len(rows),
        valid_rows=valid_rows,
        invalid_rows=len(rows) - valid_rows,
        duplicate_rows=duplicate_rows,
        rows=rows,
    )


@router.post("/import", response_model=ClientImportResult, status_code=status.HTTP_201_CREATED)
def import_clients(
    payload: ClientImportRequest,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(
        require_permissions(
            PermissionCode.CLIENT_CREATE.value,
            PermissionCode.CLIENT_EXPORT.value,
        )
    ),
):
    cpfs = [client.cpf for client in payload.clients]
    repeated_cpfs: set[str] = set()
    seen_cpfs: set[str] = set()
    for cpf in cpfs:
        if cpf in seen_cpfs:
            repeated_cpfs.add(cpf)
        seen_cpfs.add(cpf)
    if repeated_cpfs:
        raise HTTPException(status_code=409, detail="O arquivo contém CPFs repetidos. Faça uma nova conferência.")

    existing_cpfs = set(
        db.scalars(
            select(Client.cpf).where(
                Client.organization_id == identity.organization_id,
                Client.cpf.in_(set(cpfs)),
            )
        )
    )
    if existing_cpfs:
        raise HTTPException(
            status_code=409,
            detail="Um ou mais CPFs já foram cadastrados. Faça uma nova conferência do CSV.",
        )

    clients = [
        Client(
            organization_id=identity.organization_id,
            **client.model_dump(mode="python"),
        )
        for client in payload.clients
    ]
    db.add_all(clients)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A importação encontrou um CPF já cadastrado. Confira o arquivo novamente.",
        ) from exc

    record_audit(
        db,
        organization_id=identity.organization_id,
        user_id=identity.user_id,
        entity_type="client",
        entity_id=None,
        action="import",
        new_values={
            "count": len(clients),
            "source_filename": _safe_import_filename(payload.source_filename),
        },
    )
    db.commit()
    return ClientImportResult(
        imported=len(clients),
        client_ids=[client.id for client in clients],
    )


@router.get("/{client_id}", response_model=ClientRead)
def get_client(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_READ.value)
    ),
):
    client = db.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.organization_id == actor.organization_id,
            Client.archived_at.is_(None),
        )
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


@router.get("/{client_id}/profile", response_model=ClientProfileSummary)
def get_client_profile(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_READ.value)
    ),
):
    client = db.scalar(select(Client).where(
        Client.id == client_id,
        Client.organization_id == actor.organization_id,
        Client.archived_at.is_(None),
    ))
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    lead_row = db.execute(
        select(Lead, LeadSource.name, ServiceType.name, User.full_name)
        .join(LeadSource, LeadSource.id == Lead.source_id)
        .join(ServiceType, ServiceType.id == Lead.service_type_id)
        .outerjoin(User, User.id == Lead.owner_id)
        .where(
            Lead.organization_id == actor.organization_id,
            Lead.client_id == client_id,
            Lead.deleted_at.is_(None),
        )
        .order_by(Lead.updated_at.desc())
        .limit(1)
    ).first()
    lead = lead_row[0] if lead_row else None
    lead_item = ClientProfileItem(
        id=lead.id,
        title=lead_row[2],
        subtitle=f"Origem: {lead_row[1]} · Responsável: {lead_row[3] or 'Não definido'}",
        status=lead.status,
        occurred_at=lead.created_at,
    ) if lead_row else None

    contract = db.scalar(select(CommercialContract).where(
        CommercialContract.organization_id == actor.organization_id,
        CommercialContract.client_id == client_id,
        CommercialContract.deleted_at.is_(None),
    ).order_by(CommercialContract.updated_at.desc()).limit(1))
    contract_item = ClientProfileItem(
        id=contract.id,
        lead_id=contract.lead_id,
        title=contract.contract_number,
        subtitle=contract.title,
        status=contract.status,
        occurred_at=contract.updated_at,
    ) if contract else None

    recovery = db.execute(
        select(RecoveryCase, User.full_name)
        .outerjoin(User, User.id == RecoveryCase.assigned_user_id)
        .where(
            RecoveryCase.organization_id == actor.organization_id,
            RecoveryCase.client_id == client_id,
            RecoveryCase.deleted_at.is_(None),
        )
        .order_by(RecoveryCase.updated_at.desc())
        .limit(1)
    ).first()
    recovery_item = ClientProfileItem(
        id=recovery[0].id,
        title=recovery[0].case_number,
        subtitle=f"Etapa: {recovery[0].stage} · Responsável: {recovery[1] or 'Não definido'}",
        status=recovery[0].status,
        occurred_at=recovery[0].updated_at,
    ) if recovery else None

    next_task = None
    if lead:
        next_task = db.scalar(select(LeadTask).where(
            LeadTask.organization_id == actor.organization_id,
            LeadTask.lead_id == lead.id,
            LeadTask.status == "PENDENTE",
        ).order_by(LeadTask.due_at.asc()).limit(1))
    next_action_item = ClientProfileItem(
        id=next_task.id,
        title=next_task.description,
        subtitle="Próxima ação comercial",
        status=next_task.status,
        occurred_at=next_task.due_at,
    ) if next_task else None

    latest_diagnosis = db.scalar(select(Diagnosis).where(
        Diagnosis.organization_id == actor.organization_id,
        Diagnosis.client_id == client_id,
    ).order_by(Diagnosis.created_at.desc()).limit(1))
    diagnosis_item = ClientProfileItem(
        id=latest_diagnosis.id,
        title=latest_diagnosis.eligibility_result,
        subtitle=f"Versão {latest_diagnosis.version} · {latest_diagnosis.eligibility_score} pontos",
        status=latest_diagnosis.risk_level,
        occurred_at=latest_diagnosis.created_at,
    ) if latest_diagnosis else None

    timeline: list[ClientProfileItem] = []
    if lead:
        interactions = list(db.scalars(select(LeadInteraction).where(
            LeadInteraction.organization_id == actor.organization_id,
            LeadInteraction.lead_id == lead.id,
        ).order_by(LeadInteraction.occurred_at.desc()).limit(30)))
        timeline.extend(ClientProfileItem(
            id=item.id, title=item.description, subtitle="Histórico comercial",
            status=item.interaction_type, occurred_at=item.occurred_at,
        ) for item in interactions)
    if contract_item:
        timeline.append(ClientProfileItem(id=contract_item.id, title=f"Contrato {contract_item.title}", subtitle=contract_item.subtitle, status=contract_item.status, occurred_at=contract_item.occurred_at))
    if recovery_item:
        timeline.append(ClientProfileItem(id=recovery_item.id, title=f"Caso {recovery_item.title}", subtitle=recovery_item.subtitle, status=recovery_item.status, occurred_at=recovery_item.occurred_at))
    if diagnosis_item:
        timeline.append(ClientProfileItem(id=diagnosis_item.id, title="Diagnóstico financeiro salvo", subtitle=diagnosis_item.subtitle, status=diagnosis_item.status, occurred_at=diagnosis_item.occurred_at))
    # Select metadata only: document contents must not be loaded for this summary.
    documents = db.execute(select(ClientDocument.id, ClientDocument.filename, ClientDocument.status, ClientDocument.created_at).where(
        ClientDocument.organization_id == actor.organization_id,
        ClientDocument.client_id == client_id, ClientDocument.deleted_at.is_(None),
    ).order_by(ClientDocument.created_at.desc()).limit(40)).all()
    timeline.extend(ClientProfileItem(id=row.id, title=f"Documento: {row.filename}", subtitle="Documento recebido", status=row.status, occurred_at=row.created_at) for row in documents)
    negotiations = db.execute(select(Negotiation.id, Negotiation.status, Negotiation.opened_at).where(
        Negotiation.organization_id == actor.organization_id, Negotiation.client_id == client_id,
    ).order_by(Negotiation.opened_at.desc()).limit(40)).all()
    timeline.extend(ClientProfileItem(id=row.id, title="Negociação aberta", subtitle="Negociação com credor", status=row.status, occurred_at=row.opened_at) for row in negotiations)
    agreements = db.execute(select(PaymentAgreement.id, PaymentAgreement.title, PaymentAgreement.status, PaymentAgreement.created_at).where(
        PaymentAgreement.organization_id == actor.organization_id, PaymentAgreement.client_id == client_id,
    ).order_by(PaymentAgreement.created_at.desc()).limit(40)).all()
    timeline.extend(ClientProfileItem(id=row.id, title=f"Acordo: {row.title}", subtitle="Acordo registrado", status=row.status, occurred_at=row.created_at) for row in agreements)
    timeline.sort(key=lambda item: item.occurred_at.replace(tzinfo=timezone.utc).timestamp() if item.occurred_at and item.occurred_at.tzinfo is None else item.occurred_at.timestamp() if item.occurred_at else 0, reverse=True)

    document_count = db.scalar(select(func.count(ClientDocument.id)).where(
        ClientDocument.organization_id == actor.organization_id,
        ClientDocument.client_id == client_id,
        ClientDocument.deleted_at.is_(None),
    )) or 0
    negotiation_count = db.scalar(select(func.count(Negotiation.id)).where(
        Negotiation.organization_id == actor.organization_id,
        Negotiation.client_id == client_id,
    )) or 0
    agreement_count = db.scalar(select(func.count(PaymentAgreement.id)).where(
        PaymentAgreement.organization_id == actor.organization_id,
        PaymentAgreement.client_id == client_id,
    )) or 0

    return ClientProfileSummary(
        lead=lead_item,
        contract=contract_item,
        recovery_case=recovery_item,
        next_action=next_action_item,
        latest_diagnosis=diagnosis_item,
        document_count=document_count,
        negotiation_count=negotiation_count,
        agreement_count=agreement_count,
        timeline=timeline[:40],
    )


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(
    client_id: uuid.UUID,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    actor: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_UPDATE.value)
    ),
):
    client = db.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.organization_id == actor.organization_id,
            Client.archived_at.is_(None),
        )
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    changes = payload.model_dump(exclude_unset=True, mode="json")
    for key, value in changes.items():
        setattr(client, key, value)
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.user_id,
        entity_type="client",
        entity_id=client.id,
        action="update",
        new_values=changes,
    )
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_DELETE.value)
    ),
):
    client = db.scalar(
        select(Client)
        .where(
            Client.id == client_id,
            Client.organization_id == identity.organization_id,
        )
        .with_for_update()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    client_name = client.full_name
    client.archived_at = datetime.now(timezone.utc)
    record_audit(
        db,
        organization_id=identity.organization_id,
        user_id=identity.user_id,
        entity_type="client",
        entity_id=client.id,
        action="archive",
        new_values={"full_name": client_name, "archived_at": client.archived_at.isoformat()},
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{client_id}/restore", response_model=ClientRead)
def restore_client(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(
        require_permissions(PermissionCode.CLIENT_RESTORE.value)
    ),
):
    client = db.scalar(
        select(Client)
        .where(
            Client.id == client_id,
            Client.organization_id == identity.organization_id,
            Client.archived_at.is_not(None),
        )
        .with_for_update()
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente arquivado não encontrado")
    previous_archived_at = client.archived_at
    client.archived_at = None
    record_audit(
        db,
        organization_id=identity.organization_id,
        user_id=identity.user_id,
        entity_type="client",
        entity_id=client.id,
        action="restore",
        new_values={"archived_at": None, "previous_archived_at": previous_archived_at.isoformat()},
    )
    db.commit()
    db.refresh(client)
    return client
