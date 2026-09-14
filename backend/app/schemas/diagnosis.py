import uuid
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
class DiagnosisPreview(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    total_debt_balance: Decimal
    total_installments: Decimal
    disposable_income: Decimal
    commitment_percentage: Decimal
    minimum_existential_reference: Decimal
    eligibility_score: int
    eligibility_result: str
    economic_conclusion: str
    legal_alerts: list[str]
    eligible_debts: int
    attention_debts: int
    chart_data: dict
class DiagnosisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    client_id: uuid.UUID
    version: int
    total_income: Decimal
    total_expenses: Decimal
    total_debt_balance: Decimal
    total_installments: Decimal
    disposable_income: Decimal
    commitment_percentage: Decimal
    minimum_existential_reference: Decimal
    eligibility_score: int
    eligibility_result: str
    economic_conclusion: str
    legal_alerts: str
