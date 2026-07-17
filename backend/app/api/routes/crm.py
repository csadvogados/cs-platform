from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_identity_context
from app.db.session import get_db
from app.models.crm import CRMContact, CRMInteraction, CRMOpportunity, CRMTask
from app.schemas.crm import ContactCreate, ContactRead, InteractionCreate, InteractionRead, OpportunityCreate, OpportunityRead, OpportunityUpdate, TaskCreate, TaskRead, CRMSummary
from app.security.identity import IdentityContext
router=APIRouter()

def tenant(model, db, ident, item_id):
 obj=db.scalar(select(model).where(model.id==item_id,model.organization_id==ident.organization_id))
 if not obj: raise HTTPException(404,'Registro CRM não encontrado')
 return obj

@router.get('/contacts',response_model=list[ContactRead])
def list_contacts(search:str|None=None,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 q=select(CRMContact).where(CRMContact.organization_id==ident.organization_id)
 if search: q=q.where(CRMContact.name.ilike(f'%{search}%'))
 return list(db.scalars(q.order_by(CRMContact.name).offset(offset).limit(limit)))
@router.post('/contacts',response_model=ContactRead,status_code=201)
def create_contact(payload:ContactCreate,db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 obj=CRMContact(organization_id=ident.organization_id,**payload.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@router.get('/contacts/{item_id}',response_model=ContactRead)
def get_contact(item_id:UUID,db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)): return tenant(CRMContact,db,ident,item_id)
@router.delete('/contacts/{item_id}',status_code=204)
def delete_contact(item_id:UUID,db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 db.delete(tenant(CRMContact,db,ident,item_id)); db.commit()

@router.get('/interactions',response_model=list[InteractionRead])
def list_interactions(client_id:UUID|None=None,db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 q=select(CRMInteraction).where(CRMInteraction.organization_id==ident.organization_id)
 if client_id:q=q.where(CRMInteraction.client_id==client_id)
 return list(db.scalars(q.order_by(CRMInteraction.occurred_at.desc()).limit(100)))
@router.post('/interactions',response_model=InteractionRead,status_code=201)
def create_interaction(payload:InteractionCreate,db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 obj=CRMInteraction(organization_id=ident.organization_id,user_id=ident.user_id,**payload.model_dump());db.add(obj);db.commit();db.refresh(obj);return obj

@router.get('/opportunities',response_model=list[OpportunityRead])
def list_opportunities(stage:str|None=None,db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 q=select(CRMOpportunity).where(CRMOpportunity.organization_id==ident.organization_id)
 if stage:q=q.where(CRMOpportunity.stage==stage)
 return list(db.scalars(q.order_by(CRMOpportunity.updated_at.desc()).limit(100)))
@router.post('/opportunities',response_model=OpportunityRead,status_code=201)
def create_opportunity(payload:OpportunityCreate,db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 obj=CRMOpportunity(organization_id=ident.organization_id,**payload.model_dump());db.add(obj);db.commit();db.refresh(obj);return obj
@router.patch('/opportunities/{item_id}',response_model=OpportunityRead)
def update_opportunity(item_id:UUID,payload:OpportunityUpdate,db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 obj=tenant(CRMOpportunity,db,ident,item_id)
 for k,v in payload.model_dump(exclude_unset=True).items():setattr(obj,k,v)
 db.commit();db.refresh(obj);return obj

@router.get('/tasks',response_model=list[TaskRead])
def list_tasks(task_status:str|None=Query(None,alias='status'),db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 q=select(CRMTask).where(CRMTask.organization_id==ident.organization_id)
 if task_status:q=q.where(CRMTask.status==task_status)
 return list(db.scalars(q.order_by(CRMTask.due_at.asc()).limit(100)))
@router.post('/tasks',response_model=TaskRead,status_code=201)
def create_task(payload:TaskCreate,db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 obj=CRMTask(organization_id=ident.organization_id,**payload.model_dump());db.add(obj);db.commit();db.refresh(obj);return obj
@router.post('/tasks/{item_id}/complete',response_model=TaskRead)
def complete_task(item_id:UUID,db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 obj=tenant(CRMTask,db,ident,item_id);obj.status='completed';obj.completed_at=datetime.now(timezone.utc);db.commit();db.refresh(obj);return obj

@router.get('/summary',response_model=CRMSummary)
def summary(db:Session=Depends(get_db),ident:IdentityContext=Depends(get_identity_context)):
 org=ident.organization_id
 count=lambda model: db.scalar(select(func.count()).select_from(model).where(model.organization_id==org)) or 0
 value=db.scalar(select(func.coalesce(func.sum(CRMOpportunity.estimated_value),0)).where(CRMOpportunity.organization_id==org,CRMOpportunity.stage.notin_(['won','lost']))) or 0
 pending=db.scalar(select(func.count()).select_from(CRMTask).where(CRMTask.organization_id==org,CRMTask.status!='completed')) or 0
 return CRMSummary(contacts=count(CRMContact),interactions=count(CRMInteraction),opportunities=count(CRMOpportunity),open_pipeline_value=float(value),pending_tasks=pending)
