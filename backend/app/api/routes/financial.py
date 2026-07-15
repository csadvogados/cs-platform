import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.client import Client
from app.models.financial import Income, Expense, Creditor, Debt
from app.models.user import User
from app.schemas.financial import IncomeCreate, IncomeRead, ExpenseCreate, ExpenseRead, CreditorCreate, CreditorRead, DebtCreate, DebtRead
from app.services.audit import record_audit
router=APIRouter()
def owned_client(db, client_id, org_id):
    c=db.scalar(select(Client).where(Client.id==client_id,Client.organization_id==org_id))
    if not c: raise HTTPException(404,'Cliente não encontrado')
    return c
@router.post('/clients/{client_id}/incomes',response_model=IncomeRead,status_code=201)
def add_income(client_id:uuid.UUID,payload:IncomeCreate,db:Session=Depends(get_db),actor:User=Depends(require_roles('admin','lawyer','team'))):
    owned_client(db,client_id,actor.organization_id); x=Income(client_id=client_id,**payload.model_dump()); db.add(x); db.flush(); record_audit(db,organization_id=actor.organization_id,user_id=actor.id,entity_type='income',entity_id=x.id,action='create',new_values={'amount':str(x.net_amount)}); db.commit(); db.refresh(x); return x
@router.get('/clients/{client_id}/incomes',response_model=list[IncomeRead])
def list_incomes(client_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    owned_client(db,client_id,actor.organization_id); return list(db.scalars(select(Income).where(Income.client_id==client_id)))
@router.post('/clients/{client_id}/expenses',response_model=ExpenseRead,status_code=201)
def add_expense(client_id:uuid.UUID,payload:ExpenseCreate,db:Session=Depends(get_db),actor:User=Depends(require_roles('admin','lawyer','team'))):
    owned_client(db,client_id,actor.organization_id); x=Expense(client_id=client_id,**payload.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
@router.get('/clients/{client_id}/expenses',response_model=list[ExpenseRead])
def list_expenses(client_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    owned_client(db,client_id,actor.organization_id); return list(db.scalars(select(Expense).where(Expense.client_id==client_id)))
@router.post('/creditors',response_model=CreditorRead,status_code=201)
def add_creditor(payload:CreditorCreate,db:Session=Depends(get_db),actor:User=Depends(require_roles('admin','lawyer','team'))):
    x=Creditor(organization_id=actor.organization_id,**payload.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
@router.get('/creditors',response_model=list[CreditorRead])
def list_creditors(db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    return list(db.scalars(select(Creditor).where(Creditor.organization_id==actor.organization_id).order_by(Creditor.legal_name)))
@router.post('/clients/{client_id}/debts',response_model=DebtRead,status_code=201)
def add_debt(client_id:uuid.UUID,payload:DebtCreate,db:Session=Depends(get_db),actor:User=Depends(require_roles('admin','lawyer','team'))):
    owned_client(db,client_id,actor.organization_id)
    if payload.creditor_id and not db.scalar(select(Creditor).where(Creditor.id==payload.creditor_id,Creditor.organization_id==actor.organization_id)): raise HTTPException(404,'Credor não encontrado')
    x=Debt(organization_id=actor.organization_id,client_id=client_id,**payload.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
@router.get('/clients/{client_id}/debts',response_model=list[DebtRead])
def list_debts(client_id:uuid.UUID,db:Session=Depends(get_db),actor:User=Depends(get_current_user)):
    owned_client(db,client_id,actor.organization_id); return list(db.scalars(select(Debt).where(Debt.client_id==client_id,Debt.organization_id==actor.organization_id)))
