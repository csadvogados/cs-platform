from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
class ORMModel(BaseModel): model_config=ConfigDict(from_attributes=True)
class ContactCreate(BaseModel):
 client_id: UUID|None=None; name:str=Field(min_length=2,max_length=200); email:str|None=None; phone:str|None=None; position:str|None=None; notes:str|None=None
class ContactRead(ContactCreate,ORMModel): id:UUID; organization_id:UUID; created_at:datetime; updated_at:datetime
class InteractionCreate(BaseModel):
 client_id:UUID; interaction_type:str=Field(min_length=2,max_length=50); subject:str=Field(min_length=2,max_length=200); description:str|None=None; occurred_at:datetime
class InteractionRead(InteractionCreate,ORMModel): id:UUID; organization_id:UUID; user_id:UUID|None=None; created_at:datetime; updated_at:datetime
class OpportunityCreate(BaseModel):
 client_id:UUID; owner_id:UUID|None=None; title:str=Field(min_length=2,max_length=200); stage:str='lead'; estimated_value:float=Field(default=0,ge=0); probability:int=Field(default=0,ge=0,le=100); expected_close_date:date|None=None; notes:str|None=None
class OpportunityUpdate(BaseModel):
 title:str|None=None; stage:str|None=None; estimated_value:float|None=Field(default=None,ge=0); probability:int|None=Field(default=None,ge=0,le=100); expected_close_date:date|None=None; notes:str|None=None; owner_id:UUID|None=None
class OpportunityRead(OpportunityCreate,ORMModel): id:UUID; organization_id:UUID; created_at:datetime; updated_at:datetime
class TaskCreate(BaseModel):
 client_id:UUID|None=None; opportunity_id:UUID|None=None; assigned_to_id:UUID|None=None; title:str=Field(min_length=2,max_length=200); description:str|None=None; status:str='pending'; priority:str='normal'; due_at:datetime|None=None
class TaskRead(TaskCreate,ORMModel): id:UUID; organization_id:UUID; completed_at:datetime|None=None; created_at:datetime; updated_at:datetime
class CRMSummary(BaseModel): contacts:int; interactions:int; opportunities:int; open_pipeline_value:float; pending_tasks:int
