import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.client import Client
from app.models.document import ClientDocument
from app.schemas.document import DocumentRead, DocumentValidation, JudicialChecklist
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode
from app.services.audit import record_audit

router = APIRouter()
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}
REQUIRED_CATEGORIES = ["identification", "income_proof", "residence_proof", "debt_statement"]


def owned_client(db: Session, client_id: uuid.UUID, organization_id: uuid.UUID) -> Client:
    client = db.scalar(select(Client).where(Client.id == client_id, Client.organization_id == organization_id, Client.archived_at.is_(None)))
    if not client:
        raise HTTPException(404, "Cliente não encontrado")
    return client


def safe_filename(value: str | None) -> str:
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", str(value or "documento"))
    return name[:255] or "documento"


@router.post("/clients/{client_id}", response_model=DocumentRead, status_code=201)
async def upload_document(client_id: uuid.UUID, category: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), identity: IdentityContext = Depends(require_permissions(PermissionCode.DOCUMENT_UPLOAD.value))):
    owned_client(db, client_id, identity.organization_id)
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(422, "Envie um arquivo PDF, JPG ou PNG")
    content = await file.read(MAX_FILE_SIZE + 1)
    await file.close()
    if not content:
        raise HTTPException(422, "O arquivo está vazio")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(422, "O arquivo deve ter no máximo 10 MB")
    document = ClientDocument(organization_id=identity.organization_id, client_id=client_id, uploaded_by_id=identity.user_id, category=category.strip().lower(), filename=safe_filename(file.filename), content_type=file.content_type, size_bytes=len(content), content=content)
    db.add(document); db.flush()
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id, entity_type="document", entity_id=document.id, action="upload", new_values={"client_id": str(client_id), "category": document.category, "filename": document.filename, "size_bytes": document.size_bytes})
    db.commit(); db.refresh(document)
    return document


@router.get("/clients/{client_id}", response_model=list[DocumentRead])
def list_documents(client_id: uuid.UUID, db: Session = Depends(get_db), identity: IdentityContext = Depends(require_permissions(PermissionCode.DOCUMENT_READ.value))):
    owned_client(db, client_id, identity.organization_id)
    return list(db.scalars(select(ClientDocument).where(ClientDocument.client_id == client_id, ClientDocument.organization_id == identity.organization_id, ClientDocument.deleted_at.is_(None)).order_by(ClientDocument.created_at.desc())))


@router.get("/{document_id}/download")
def download_document(document_id: uuid.UUID, db: Session = Depends(get_db), identity: IdentityContext = Depends(require_permissions(PermissionCode.DOCUMENT_READ.value))):
    document = db.scalar(select(ClientDocument).where(ClientDocument.id == document_id, ClientDocument.organization_id == identity.organization_id, ClientDocument.deleted_at.is_(None)))
    if not document: raise HTTPException(404, "Documento não encontrado")
    return Response(document.content, media_type=document.content_type, headers={"Content-Disposition": f'inline; filename="{document.filename}"', "Cache-Control": "no-store"})


@router.post("/{document_id}/validation", response_model=DocumentRead)
def validate_document(document_id: uuid.UUID, payload: DocumentValidation, db: Session = Depends(get_db), identity: IdentityContext = Depends(require_permissions(PermissionCode.DOCUMENT_VALIDATE.value))):
    document = db.scalar(select(ClientDocument).where(ClientDocument.id == document_id, ClientDocument.organization_id == identity.organization_id, ClientDocument.deleted_at.is_(None)))
    if not document: raise HTTPException(404, "Documento não encontrado")
    document.status = payload.status; document.validation_notes = payload.notes; document.validated_by_id = identity.user_id; document.validated_at = datetime.now(timezone.utc)
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id, entity_type="document", entity_id=document.id, action="validate", new_values={"status": document.status, "notes": payload.notes})
    db.commit(); db.refresh(document)
    return document


@router.get("/clients/{client_id}/judicial-checklist", response_model=JudicialChecklist)
def judicial_checklist(client_id: uuid.UUID, db: Session = Depends(get_db), identity: IdentityContext = Depends(require_permissions(PermissionCode.DOCUMENT_READ.value))):
    owned_client(db, client_id, identity.organization_id)
    documents = list(db.scalars(select(ClientDocument).where(ClientDocument.client_id == client_id, ClientDocument.organization_id == identity.organization_id, ClientDocument.deleted_at.is_(None))))
    validated = sorted({item.category for item in documents if item.status == "validated"})
    rejected = sorted({item.category for item in documents if item.status == "rejected"})
    missing = [item for item in REQUIRED_CATEGORIES if item not in validated]
    return JudicialChecklist(client_id=client_id, required_categories=REQUIRED_CATEGORIES, validated_categories=validated, missing_categories=missing, rejected_categories=rejected, ready=not missing)
