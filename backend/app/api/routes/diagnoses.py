import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.client import Client
from app.models.financial import Diagnosis
from app.models.user import User
from app.schemas.diagnosis import DiagnosisPreview, DiagnosisRead
from app.services.diagnosis_engine import calculate
from app.services.report_service import economic_report
router=APIRouter()
def loaded(db,client_id,org_id):
    c=db.scalar(select(Client).where(Client.id==client_id,Client.organization_id==org_id).options(selectinload(Client.incomes),selectinload(Client.expenses),selectinload(Client.debts)))
    if not c: raise HTTPException(404,'Cliente não encontrado')
    return c
@router.get('/{client_id}/preview',response_model=DiagnosisPreview)
def preview(client_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    return calculate(loaded(db,client_id,actor.organization_id),Decimal(str(settings.minimum_existential_reference)))
@router.post('/{client_id}',response_model=DiagnosisRead,status_code=201)
def save(client_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(require_roles('admin','lawyer'))):
    c=loaded(db,client_id,actor.organization_id); d=calculate(c,Decimal(str(settings.minimum_existential_reference))); version=(db.scalar(select(func.max(Diagnosis.version)).where(Diagnosis.client_id==client_id)) or 0)+1
    x=Diagnosis(organization_id=actor.organization_id,client_id=client_id,version=version,total_income=d['total_income'],total_expenses=d['total_expenses'],total_debt_balance=d['total_debt_balance'],total_installments=d['total_installments'],disposable_income=d['disposable_income'],commitment_percentage=d['commitment_percentage'],minimum_existential_reference=d['minimum_existential_reference'],eligibility_score=d['eligibility_score'],eligibility_result=d['eligibility_result'],economic_conclusion=d['economic_conclusion'],legal_alerts='\n'.join(d['legal_alerts']))
    db.add(x); db.commit(); db.refresh(x); return x
@router.get('/{client_id}/report',response_class=Response)
def report(client_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    c=loaded(db,client_id,actor.organization_id); return Response(economic_report(c,calculate(c,Decimal(str(settings.minimum_existential_reference)))),media_type='text/html')
