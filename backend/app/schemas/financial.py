import uuid
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
class ORM(BaseModel): model_config = ConfigDict(from_attributes=True)
class IncomeCreate(BaseModel):
    income_type: str
    description: str | None = None
    net_amount: Decimal = Field(ge=0)
    recurring: bool = True
class IncomeRead(IncomeCreate, ORM): id: uuid.UUID; client_id: uuid.UUID
class ExpenseCreate(BaseModel):
    category: str
    description: str | None = None
    amount: Decimal = Field(ge=0)
    essential: bool = True
    recurring: bool = True
class ExpenseRead(ExpenseCreate, ORM): id: uuid.UUID; client_id: uuid.UUID
class CreditorCreate(BaseModel):
    legal_name: str
    sac_phone: str | None = None
    sac_email: str | None = None
    ombudsman_phone: str | None = None
    ombudsman_email: str | None = None
    consumer_gov_enabled: bool = False
class CreditorRead(CreditorCreate, ORM): id: uuid.UUID; organization_id: uuid.UUID
class DebtCreate(BaseModel):
    creditor_id: uuid.UUID | None = None
    nature: str
    current_balance: Decimal = Field(default=0, ge=0)
    monthly_installment: Decimal = Field(default=0, ge=0)
    overdue: bool = False
class DebtRead(DebtCreate, ORM): id: uuid.UUID; organization_id: uuid.UUID; client_id: uuid.UUID
