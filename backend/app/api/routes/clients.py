import csv
import io
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permissions, require_roles
from app.db.session import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
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


def _client_query(organization_id: uuid.UUID, query: str | None, client_status: str | None):
    stmt = select(Client).where(Client.organization_id == organization_id)
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
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
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
        user_id=actor.id,
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
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    stmt = (
        _client_query(actor.organization_id, q, client_status)
        .order_by(Client.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


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


@router.get("/{client_id}", response_model=ClientRead)
def get_client(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    client = db.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.organization_id == actor.organization_id,
        )
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(
    client_id: uuid.UUID,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    client = db.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.organization_id == actor.organization_id,
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
        user_id=actor.id,
        entity_type="client",
        entity_id=client.id,
        action="update",
        new_values=changes,
    )
    db.commit()
    db.refresh(client)
    return client
