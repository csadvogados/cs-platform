import calendar
import csv
import io
import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions, require_roles
from app.db.session import get_db
from app.models.client import Client
from app.models.crm import CRMInteraction, CRMOpportunity, CRMTask
from app.models.financial import PaymentInstallment
from app.models.performance import PerformanceGoal
from app.models.user import User
from app.schemas.performance import (
    PerformanceAlertRead,
    PerformanceGoalRead,
    PerformanceGoalUpsert,
    PerformanceMetricRead,
    PerformanceOverviewRead,
    PerformanceRankingRead,
)
from app.security.identity import IdentityContext
from app.services.audit import record_audit


router = APIRouter()
METRIC_LABELS = {
    "new_clients": "Novos clientes",
    "interactions": "Atendimentos",
    "completed_tasks": "Tarefas concluídas",
    "received_amount": "Recebimentos",
    "won_opportunities": "Oportunidades ganhas",
}
MONEY_METRICS = {"received_amount"}
CENT = Decimal("0.01")


def normalized_month(value: date | None) -> date:
    selected = value or date.today().replace(day=1)
    return selected.replace(day=1)


def month_bounds(reference: date) -> tuple[date, date]:
    last_day = calendar.monthrange(reference.year, reference.month)[1]
    return reference, reference.replace(day=last_day)


def datetime_bounds(start: date, end: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(start, time.min, tzinfo=timezone.utc),
        datetime.combine(end, time.max, tzinfo=timezone.utc),
    )


def decimal_value(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENT, rounding=ROUND_HALF_UP)


def actual_metrics(
    db: Session,
    organization_id: uuid.UUID,
    start: date,
    end: date,
    user_id: uuid.UUID | None = None,
) -> dict[str, Decimal]:
    start_dt, end_dt = datetime_bounds(start, end)

    client_query = select(func.count(Client.id)).where(
        Client.organization_id == organization_id,
        Client.created_at >= start_dt,
        Client.created_at <= end_dt,
    )
    interaction_query = select(func.count(CRMInteraction.id)).where(
        CRMInteraction.organization_id == organization_id,
        CRMInteraction.occurred_at >= start_dt,
        CRMInteraction.occurred_at <= end_dt,
    )
    task_query = select(func.count(CRMTask.id)).where(
        CRMTask.organization_id == organization_id,
        CRMTask.status == "completed",
        CRMTask.completed_at >= start_dt,
        CRMTask.completed_at <= end_dt,
    )
    received_query = select(func.coalesce(func.sum(PaymentInstallment.paid_amount), 0)).where(
        PaymentInstallment.organization_id == organization_id,
        PaymentInstallment.status == "paid",
        PaymentInstallment.paid_at >= start_dt,
        PaymentInstallment.paid_at <= end_dt,
    )
    won_query = select(func.count(CRMOpportunity.id)).where(
        CRMOpportunity.organization_id == organization_id,
        CRMOpportunity.stage == "won",
        CRMOpportunity.updated_at >= start_dt,
        CRMOpportunity.updated_at <= end_dt,
    )
    if user_id:
        client_query = client_query.where(Client.assigned_user_id == user_id)
        interaction_query = interaction_query.where(CRMInteraction.user_id == user_id)
        task_query = task_query.where(CRMTask.assigned_to_id == user_id)
        received_query = received_query.where(PaymentInstallment.collection_assigned_user_id == user_id)
        won_query = won_query.where(CRMOpportunity.owner_id == user_id)

    return {
        "new_clients": decimal_value(db.scalar(client_query)),
        "interactions": decimal_value(db.scalar(interaction_query)),
        "completed_tasks": decimal_value(db.scalar(task_query)),
        "received_amount": decimal_value(db.scalar(received_query)),
        "won_opportunities": decimal_value(db.scalar(won_query)),
    }


def goal_read(goal: PerformanceGoal, users: dict[uuid.UUID, str]) -> PerformanceGoalRead:
    return PerformanceGoalRead(
        id=goal.id,
        reference_month=goal.reference_month,
        metric=goal.metric,
        target_value=goal.target_value,
        user_id=goal.user_id,
        user_name=users.get(goal.user_id) if goal.user_id else None,
    )


def metric_read(metric: str, target: Decimal, actual: Decimal, elapsed: Decimal) -> PerformanceMetricRead:
    progress = (actual / target * 100) if target > 0 else Decimal("0")
    projection = (actual / elapsed * 100) if elapsed > 0 else actual
    projected_percent = (projection / target * 100) if target > 0 else Decimal("0")
    if target <= 0:
        metric_status = "no_goal"
    elif progress >= 100:
        metric_status = "achieved"
    elif projected_percent >= 100:
        metric_status = "on_track"
    else:
        metric_status = "attention"
    return PerformanceMetricRead(
        metric=metric,
        label=METRIC_LABELS[metric],
        target_value=decimal_value(target),
        actual_value=decimal_value(actual),
        progress_percent=decimal_value(progress),
        projected_value=decimal_value(projection),
        projected_percent=decimal_value(projected_percent),
        status=metric_status,
    )


def build_overview(db: Session, identity: IdentityContext, reference_month: date) -> PerformanceOverviewRead:
    start, month_end = month_bounds(reference_month)
    today = date.today()
    effective_end = min(today, month_end) if reference_month <= today.replace(day=1) else start
    elapsed_days = max(1, (effective_end - start).days + 1)
    total_days = (month_end - start).days + 1
    elapsed = (Decimal(elapsed_days) / Decimal(total_days) * 100).quantize(CENT)

    users_list = list(db.scalars(select(User).where(
        User.organization_id == identity.organization_id,
        User.status == "active",
        User.deleted_at.is_(None),
    ).order_by(User.full_name)))
    users = {user.id: user.full_name for user in users_list}
    goals = list(db.scalars(select(PerformanceGoal).where(
        PerformanceGoal.organization_id == identity.organization_id,
        PerformanceGoal.reference_month == reference_month,
    ).order_by(PerformanceGoal.user_id, PerformanceGoal.metric)))
    organization_goals = {goal.metric: Decimal(goal.target_value) for goal in goals if goal.user_id is None}
    organization_actual = actual_metrics(db, identity.organization_id, start, effective_end)
    organization_metrics = [
        metric_read(metric, organization_goals.get(metric, Decimal("0")), organization_actual[metric], elapsed)
        for metric in METRIC_LABELS
    ]

    user_goals: dict[uuid.UUID, list[PerformanceGoal]] = {}
    for goal in goals:
        if goal.user_id:
            user_goals.setdefault(goal.user_id, []).append(goal)

    ranking = []
    for user in users_list:
        actual = actual_metrics(db, identity.organization_id, start, effective_end, user.id)
        scoped_goals = user_goals.get(user.id, [])
        progresses = []
        achieved = 0
        for goal in scoped_goals:
            target = Decimal(goal.target_value)
            progress = (actual.get(goal.metric, Decimal("0")) / target * 100) if target else Decimal("0")
            progresses.append(min(progress, Decimal("200")))
            if progress >= 100:
                achieved += 1
        average = sum(progresses, Decimal("0")) / len(progresses) if progresses else Decimal("0")
        ranking.append(PerformanceRankingRead(
            user_id=user.id,
            user_name=user.full_name,
            goal_count=len(scoped_goals),
            average_progress=decimal_value(average),
            achieved_goals=achieved,
            interactions=int(actual["interactions"]),
            completed_tasks=int(actual["completed_tasks"]),
            won_opportunities=int(actual["won_opportunities"]),
            received_amount=actual["received_amount"],
        ))
    ranking.sort(
        key=lambda row: (row.average_progress, row.achieved_goals, row.received_amount, row.interactions),
        reverse=True,
    )

    alerts = []
    for metric in organization_metrics:
        if metric.status == "achieved":
            alerts.append(PerformanceAlertRead(
                severity="success", title=f"Meta atingida: {metric.label}",
                detail=f"Resultado de {metric.progress_percent}% da meta mensal.",
            ))
        elif metric.status == "attention":
            alerts.append(PerformanceAlertRead(
                severity="warning", title=f"Atenção em {metric.label}",
                detail=f"A projeção indica {metric.projected_percent}% da meta no fechamento do mês.",
            ))
    if not organization_goals:
        alerts.append(PerformanceAlertRead(
            severity="info", title="Defina as metas do mês",
            detail="Cadastre metas gerais para ativar o acompanhamento e as projeções.",
        ))
    elif not alerts:
        alerts.append(PerformanceAlertRead(
            severity="info", title="Desempenho dentro do planejado",
            detail="Nenhum desvio relevante foi identificado para este mês.",
        ))

    return PerformanceOverviewRead(
        reference_month=reference_month,
        period_start=start,
        period_end=month_end,
        elapsed_percent=elapsed,
        goals=[goal_read(goal, users) for goal in goals],
        organization_metrics=organization_metrics,
        ranking=ranking,
        alerts=alerts,
    )


@router.get("/overview", response_model=PerformanceOverviewRead)
def performance_overview(
    month: date | None = Query(default=None),
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions("report.read")),
):
    return build_overview(db, identity, normalized_month(month))


@router.put("/goals", response_model=PerformanceGoalRead)
def upsert_performance_goal(
    payload: PerformanceGoalUpsert,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions("report.read")),
    manager: User = Depends(require_roles("admin", "supervisor")),
):
    reference = normalized_month(payload.reference_month)
    if payload.user_id:
        user = db.scalar(select(User).where(
            User.id == payload.user_id,
            User.organization_id == identity.organization_id,
            User.status == "active",
            User.deleted_at.is_(None),
        ))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responsável não encontrado")
    query = select(PerformanceGoal).where(
        PerformanceGoal.organization_id == identity.organization_id,
        PerformanceGoal.reference_month == reference,
        PerformanceGoal.metric == payload.metric,
    )
    query = query.where(
        PerformanceGoal.user_id == payload.user_id if payload.user_id else PerformanceGoal.user_id.is_(None)
    )
    goal = db.scalar(query)
    action = "updated"
    if not goal:
        action = "created"
        goal = PerformanceGoal(
            organization_id=identity.organization_id,
            reference_month=reference,
            metric=payload.metric,
            user_id=payload.user_id,
            target_value=payload.target_value,
        )
        db.add(goal)
    else:
        goal.target_value = payload.target_value
    db.flush()
    record_audit(
        db, organization_id=identity.organization_id, user_id=identity.user_id,
        entity_type="performance_goal", entity_id=goal.id, action=action,
        new_values={"month": str(reference), "metric": payload.metric, "target": str(payload.target_value), "user_id": str(payload.user_id or "")},
    )
    db.commit()
    db.refresh(goal)
    return goal_read(goal, {payload.user_id: user.full_name} if payload.user_id else {})


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_performance_goal(
    goal_id: uuid.UUID,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions("report.read")),
    manager: User = Depends(require_roles("admin", "supervisor")),
):
    goal = db.scalar(select(PerformanceGoal).where(
        PerformanceGoal.id == goal_id,
        PerformanceGoal.organization_id == identity.organization_id,
    ))
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meta não encontrada")
    record_audit(
        db, organization_id=identity.organization_id, user_id=identity.user_id,
        entity_type="performance_goal", entity_id=goal.id, action="deleted",
        new_values={"month": str(goal.reference_month), "metric": goal.metric},
    )
    db.delete(goal)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/overview.csv")
def export_performance_overview(
    month: date | None = Query(default=None),
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions("report.read", "report.export")),
):
    report = build_overview(db, identity, normalized_month(month))
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Metas e desempenho", "CS Platform", "v5.25.0"])
    writer.writerow(["Mês", report.reference_month.strftime("%m/%Y")])
    writer.writerow([])
    writer.writerow(["Indicador", "Meta", "Realizado", "% atingido", "Projeção", "% projetado", "Situação"])
    for metric in report.organization_metrics:
        writer.writerow([
            metric.label, metric.target_value, metric.actual_value, metric.progress_percent,
            metric.projected_value, metric.projected_percent, metric.status,
        ])
    writer.writerow([])
    writer.writerow(["Ranking", "Responsável", "Metas", "Média %", "Atingidas", "Atendimentos", "Tarefas", "Vendas", "Recebimentos"])
    for position, member in enumerate(report.ranking, start=1):
        writer.writerow([
            position, member.user_name, member.goal_count, member.average_progress,
            member.achieved_goals, member.interactions, member.completed_tasks,
            member.won_opportunities, member.received_amount,
        ])
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="metas_{report.reference_month:%Y_%m}.csv"'},
    )
