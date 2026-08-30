from datetime import date

from pydantic import BaseModel, Field


class JudicialMetric(BaseModel):
    key: str
    label: str
    count: int = Field(ge=0)


class JudicialMonthlyMetric(BaseModel):
    month: str
    closed: int = Field(ge=0)


class JudicialReportRead(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    total: int = 0
    active: int = 0
    closed: int = 0
    overdue_deadlines: int = 0
    deadlines_next_7_days: int = 0
    average_duration_days: float = 0
    favorable_rate: float = 0
    outcomes: list[JudicialMetric] = Field(default_factory=list)
    statuses: list[JudicialMetric] = Field(default_factory=list)
    monthly_closures: list[JudicialMonthlyMetric] = Field(default_factory=list)
