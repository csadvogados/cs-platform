from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.client import Client
from app.models.financial import Debt, Diagnosis
from app.models.user import User
router=APIRouter()
@router.get('')
def dashboard(db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    return {'clients':db.scalar(select(func.count(Client.id)).where(Client.organization_id==actor.organization_id)) or 0,'debts':db.scalar(select(func.count(Debt.id)).where(Debt.organization_id==actor.organization_id)) or 0,'diagnoses':db.scalar(select(func.count(Diagnosis.id)).where(Diagnosis.organization_id==actor.organization_id)) or 0}
