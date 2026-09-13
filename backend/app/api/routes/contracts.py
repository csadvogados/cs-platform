from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_identity_context
from app.db.session import get_db
from app.models.client import Client
from app.models.crm import CommercialContract, Lead
from app.schemas.leads import ContractListItem, ContractRead, ContractSummary
from app.security.identity import IdentityContext

router = APIRouter()
ALLOWED_ROLES = {"admin", "supervisor", "advogado", "atendimento"}


def authorize(identity: IdentityContext):
    if not identity.is_superuser and str(identity.role).lower() not in ALLOWED_ROLES:
        raise HTTPException(403, "Perfil sem acesso aos contratos comerciais")


@router.get("/summary", response_model=ContractSummary)
def summary(db: Session = Depends(get_db), identity: IdentityContext = Depends(get_identity_context)):
    authorize(identity)
    rows = dict(db.execute(select(CommercialContract.status, func.count(CommercialContract.id)).where(
        CommercialContract.organization_id == identity.organization_id,
        CommercialContract.deleted_at.is_(None),
    ).group_by(CommercialContract.status)).all())
    return ContractSummary(
        total=sum(rows.values()), draft=rows.get("RASCUNHO", 0),
        awaiting_approval=rows.get("EM_REVISAO", 0), awaiting_signature=rows.get("ENVIADO", 0),
        signed=rows.get("ASSINADO", 0), cancelled=rows.get("CANCELADO", 0),
    )


@router.get("", response_model=list[ContractListItem])
def list_contracts(
    search: str | None = Query(None, max_length=200), status: str | None = Query(None, max_length=20),
    limit: int = Query(100, ge=1, le=200), db: Session = Depends(get_db),
    identity: IdentityContext = Depends(get_identity_context),
):
    authorize(identity)
    conditions = [CommercialContract.organization_id == identity.organization_id, CommercialContract.deleted_at.is_(None)]
    if status: conditions.append(CommercialContract.status == status)
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(CommercialContract.contract_number.ilike(term), CommercialContract.title.ilike(term), Client.full_name.ilike(term), Lead.full_name.ilike(term)))
    rows = db.execute(select(CommercialContract, Client.full_name, Lead.full_name).join(Client, Client.id == CommercialContract.client_id).join(Lead, Lead.id == CommercialContract.lead_id).where(*conditions).order_by(CommercialContract.updated_at.desc()).limit(limit)).all()
    return [ContractListItem(**ContractRead.model_validate(contract).model_dump(), client_name=client_name, lead_name=lead_name) for contract, client_name, lead_name in rows]
