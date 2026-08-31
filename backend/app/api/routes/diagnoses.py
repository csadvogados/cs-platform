import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_current_user, require_permissions, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.client import Client
from app.models.financial import Debt, Diagnosis
from app.models.user import User
from app.schemas.diagnosis import ClientDossier, DiagnosisPreview, DiagnosisRead
from app.services.diagnosis_engine import calculate
from app.services.audit import record_audit
from app.services.report_service import economic_report, saved_economic_report
from app.services.judicial_dossier import build_judicial_dossier, render_judicial_dossier
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode
router=APIRouter()
def loaded(db,client_id,org_id):
    c=db.scalar(select(Client).where(Client.id==client_id,Client.organization_id==org_id,Client.archived_at.is_(None)).options(selectinload(Client.incomes),selectinload(Client.expenses),selectinload(Client.debts).selectinload(Debt.creditor)))
    if not c: raise HTTPException(404,'Cliente não encontrado')
    return c


def build_dossier(db: Session, client: Client, organization_id: uuid.UUID) -> dict:
    summary = calculate(client, Decimal(str(settings.minimum_existential_reference)))
    latest = db.scalar(
        select(Diagnosis)
        .where(
            Diagnosis.client_id == client.id,
            Diagnosis.organization_id == organization_id,
        )
        .order_by(Diagnosis.version.desc(), Diagnosis.created_at.desc())
        .limit(1)
    )
    debts = [
        {
            "id": debt.id,
            "creditor_id": debt.creditor_id,
            "creditor_name": debt.creditor.legal_name if debt.creditor else None,
            "nature": debt.nature,
            "current_balance": debt.current_balance,
            "monthly_installment": debt.monthly_installment,
            "overdue": debt.overdue,
        }
        for debt in client.debts
    ]
    creditors = {
        debt.creditor.id: {
            "id": debt.creditor.id,
            "legal_name": debt.creditor.legal_name,
            "sac_phone": debt.creditor.sac_phone,
            "sac_email": debt.creditor.sac_email,
            "consumer_gov_enabled": debt.creditor.consumer_gov_enabled,
        }
        for debt in client.debts
        if debt.creditor is not None
    }
    missing = []
    if not client.incomes:
        missing.append("Cadastrar ao menos uma renda.")
    if not client.expenses:
        missing.append("Cadastrar despesas essenciais.")
    if not client.debts:
        missing.append("Cadastrar ao menos uma dívida.")
    if client.good_faith_declared is None:
        missing.append("Confirmar a declaração de boa-fé.")
    if client.can_pay_without_harming_basics is None:
        missing.append("Confirmar a capacidade de pagamento sem prejuízo do mínimo existencial.")
    if latest is None:
        missing.append("Salvar uma versão do diagnóstico.")
    return {
        "client": {
            "id": client.id,
            "full_name": client.full_name,
            "cpf": client.cpf,
            "birth_date": client.birth_date,
            "profession": client.profession,
            "email": client.email,
            "phone": client.phone,
            "city": client.city,
            "state": client.state,
            "person_natural": client.person_natural,
            "good_faith_declared": client.good_faith_declared,
            "can_pay_without_harming_basics": client.can_pay_without_harming_basics,
        },
        "financial_summary": summary,
        "creditors": list(creditors.values()),
        "debts": debts,
        "latest_diagnosis": latest,
        "missing_information": missing,
        "generated_at": datetime.now(timezone.utc),
    }


@router.get('/{client_id}/dossier', response_model=ClientDossier)
def dossier(client_id: uuid.UUID, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    client = loaded(db, client_id, actor.organization_id)
    return build_dossier(db, client, actor.organization_id)

@router.get('/{client_id}/judicial-dossier')
def judicial_dossier(client_id: uuid.UUID, db: Session = Depends(get_db),
                     identity: IdentityContext = Depends(require_permissions(PermissionCode.JUDICIAL_REPORT_READ.value))):
    client = loaded(db, client_id, identity.organization_id)
    return build_judicial_dossier(db, client)

@router.get('/{client_id}/judicial-dossier/report', response_class=Response)
def judicial_dossier_report(client_id: uuid.UUID, db: Session = Depends(get_db),
                            identity: IdentityContext = Depends(require_permissions(PermissionCode.JUDICIAL_REPORT_READ.value))):
    client = loaded(db, client_id, identity.organization_id)
    data = build_judicial_dossier(db, client)
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id,
                 entity_type="judicial_dossier", entity_id=client.id, action="export",
                 new_values={"ready": data["checklist"]["ready"], "missing_items": len(data["missing_information"]) + len(data["checklist"]["missing"])})
    db.commit()
    return Response(render_judicial_dossier(data), media_type='text/html',
                    headers={'Content-Disposition': f'inline; filename="dossie-judicial-{client_id}.html"', 'Cache-Control': 'no-store'})
@router.get('/{client_id}/preview',response_model=DiagnosisPreview)
def preview(client_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    return calculate(loaded(db,client_id,actor.organization_id),Decimal(str(settings.minimum_existential_reference)))
@router.post('/{client_id}',response_model=DiagnosisRead,status_code=201)
def save(client_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(require_roles('admin','lawyer'))):
    c=loaded(db,client_id,actor.organization_id); d=calculate(c,Decimal(str(settings.minimum_existential_reference))); version=(db.scalar(select(func.max(Diagnosis.version)).where(Diagnosis.client_id==client_id,Diagnosis.organization_id==actor.organization_id)) or 0)+1
    x=Diagnosis(organization_id=actor.organization_id,client_id=client_id,version=version,total_income=d['total_income'],total_expenses=d['total_expenses'],total_debt_balance=d['total_debt_balance'],total_installments=d['total_installments'],disposable_income=d['disposable_income'],commitment_percentage=d['commitment_percentage'],minimum_existential_reference=d['minimum_existential_reference'],eligibility_score=d['eligibility_score'],eligibility_result=d['eligibility_result'],economic_conclusion=d['economic_conclusion'],legal_alerts='\n'.join(d['legal_alerts']),risk_level=d['risk_level'],recommended_strategy=d['recommended_strategy'],max_payment_capacity=d['max_payment_capacity'],data_quality_score=d['data_quality_score'],score_breakdown=d['score_breakdown'],analysis_snapshot=d['analysis_snapshot'])
    db.add(x); db.flush(); record_audit(db,organization_id=actor.organization_id,user_id=actor.id,entity_type="diagnosis",entity_id=x.id,action="create",new_values={"version":version,"eligibility_score":d["eligibility_score"],"eligibility_result":d["eligibility_result"]}); db.commit(); db.refresh(x); return x
@router.get('/{client_id}/history',response_model=list[DiagnosisRead])
def history(client_id:uuid.UUID,limit:int=Query(20,ge=1,le=100),db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    loaded(db,client_id,actor.organization_id)
    return list(db.scalars(select(Diagnosis).where(Diagnosis.client_id==client_id,Diagnosis.organization_id==actor.organization_id).order_by(Diagnosis.version.desc(),Diagnosis.created_at.desc()).limit(limit)))
@router.get('/{client_id}/report',response_class=Response)
def report(client_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    c=loaded(db,client_id,actor.organization_id); return Response(economic_report(c,calculate(c,Decimal(str(settings.minimum_existential_reference)))),media_type='text/html',headers={'Content-Disposition':f'inline; filename="diagnostico-atual-{client_id}.html"'})
@router.get('/{client_id}/history/{diagnosis_id}/report',response_class=Response)
def saved_report(client_id:uuid.UUID,diagnosis_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    c=loaded(db,client_id,actor.organization_id)
    diagnosis=db.scalar(select(Diagnosis).where(Diagnosis.id==diagnosis_id,Diagnosis.client_id==client_id,Diagnosis.organization_id==actor.organization_id))
    if not diagnosis: raise HTTPException(404,'Diagnóstico não encontrado')
    return Response(saved_economic_report(c,diagnosis),media_type='text/html',headers={'Content-Disposition':f'inline; filename="diagnostico-v{diagnosis.version}-{client_id}.html"'})
