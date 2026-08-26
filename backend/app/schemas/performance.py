from datetime import date
from decimal import Decimal
from typing import Literal
import uuid

from pydantic import BaseModel, Field


PerformanceMetric = Literal[
    "new_clients", "interactions", "completed_tasks", "received_amount", "won_opportunities"
]


class PerformanceGoalUpsert(BaseModel):
    reference_month: date
    metric: PerformanceMetric
    target_value: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    user_id: uuid.UUID | None = None


class PerformanceGoalRead(PerformanceGoalUpsert):
    id: uuid.UUID
    user_name: str | None = None


class PerformanceMetricRead(BaseModel):
    metric: PerformanceMetric
    label: str
    target_value: Decimal = Decimal("0")
    actual_value: Decimal = Decimal("0")
    progress_percent: Decimal = Decimal("0")
    projected_value: Decimal = Decimal("0")
    projected_percent: Decimal = Decimal("0")
    status: Literal["no_goal", "on_track", "attention", "achieved"] = "no_goal"


class PerformanceRankingRead(BaseModel):
    user_id: uuid.UUID
    user_name: str
    goal_count: int = 0
    average_progress: Decimal = Decimal("0")
    achieved_goals: int = 0
    interactions: int = 0
    completed_tasks: int = 0
    won_opportunities: int = 0
    received_amount: Decimal = Decimal("0")


class PerformanceAlertRead(BaseModel):
    severity: Literal["info", "warning", "success"]
    title: str
    detail: str


class PerformanceOverviewRead(BaseModel):
    reference_month: date
    period_start: date
    period_end: date
    elapsed_percent: Decimal
    goals: list[PerformanceGoalRead] = Field(default_factory=list)
    organization_metrics: list[PerformanceMetricRead] = Field(default_factory=list)
    ranking: list[PerformanceRankingRead] = Field(default_factory=list)
    alerts: list[PerformanceAlertRead] = Field(default_factory=list)
