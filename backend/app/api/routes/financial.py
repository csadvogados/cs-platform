import calendar
import csv
import io
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_permissions, require_roles
from app.db.session import get_db
from app.models.client import Client
from app.models.crm import CRMInteraction, CRMOpportunity, CRMTask
from app.models.financial import CollectionAction, Creditor, Debt, Expense, Income, PaymentAgreement, PaymentInstallment
from app.models.user import User
from app.schemas.financial import (
    CreditorCreate,
    CreditorRead,
    CollectionAssignmentUpdate,
    CollectionBulkAssignmentResult,
    CollectionBulkAssignmentUpdate,
    CollectionDistributionCreate,
    CollectionDistributionResult,
    CollectionDistributionUserResult,
    CollectionItemRead,
    CollectionActionCreate,
    CollectionActionCancel,
    CollectionActionRead,
    CollectionAgingRead,
    CollectionReportRead,
    CollectionSummaryRead,
    CollectionTeamPerformanceRead,
    ExecutiveOverviewRead,
    ExecutivePipelineStageRead,
    ExecutiveTeamPerformanceRead,
    ExecutiveTrendPointRead,
    CollectionWorkloadRead,
    CollectionsRead,
    OperationalAlertRead,
    OperationalAlertsRead,
    OperationalAgendaItemRead,
    OperationalAgendaRead,
    OperationalAgendaSummaryRead,
    OperationalAgendaWorkloadRead,
    DebtCreate,
    DebtRead,
    ExpenseCreate,
    ExpenseRead,
    IncomeCreate,
    IncomeRead,
    PaymentAgreementCreate,
    PaymentAgreementRead,
    InstallmentPaymentCreate,
    PaymentInstallmentRead,
)
from app.security.identity import IdentityContext
from app.services.audit import record_audit

router = APIRouter()

CENT = Decimal("0.01")


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def build_installments(agreement: PaymentAgreement) -> list[PaymentInstallment]:
    count = max(1, agreement.installment_count)
    total = max(Decimal("0"), Decimal(agreement.negotiated_amount) - Decimal(agreement.down_payment))
    if total <= 0:
        return []
    regular = Decimal(agreement.installment_amount or 0).quantize(CENT, rounding=ROUND_HALF_UP)
    equal_amount = (total / count).quantize(CENT, rounding=ROUND_HALF_UP)
    if regular <= 0 or regular * (count - 1) >= total:
        regular = equal_amount
    start = agreement.first_due_date or date.today()
    installments: list[PaymentInstallment] = []
    allocated = Decimal("0")
    for number in range(1, count + 1):
        amount = regular if number < count else (total - allocated).quantize(CENT, rounding=ROUND_HALF_UP)
        if amount <= 0:
            amount = equal_amount
        allocated += amount
        installments.append(PaymentInstallment(
            organization_id=agreement.organization_id,
            client_id=agreement.client_id,
            agreement_id=agreement.id,
            installment_number=number,
            due_date=add_months(start, number - 1),
            amount=amount,
            status="pending",
            paid_amount=Decimal("0"),
        ))
    return installments


def sync_installment_statuses(agreement: PaymentAgreement) -> bool:
    changed = False
    today = date.today()
    for installment in agreement.installments:
        if installment.status in {"paid", "cancelled"}:
            continue
        expected = "overdue" if installment.due_date < today else "pending"
        if installment.status != expected:
            installment.status = expected
            changed = True
    return changed


def collection_status(installment: PaymentInstallment, today: date) -> str:
    if installment.status in {"paid", "cancelled"}:
        return installment.status
    if installment.due_date < today:
        return "overdue"
    if installment.due_date <= today + timedelta(days=7):
        return "due_soon"
    return "pending"


def collection_aging_bucket(due_date: date, today: date) -> str | None:
    overdue_days = (today - due_date).days
    if overdue_days < 1:
        return None
    if overdue_days <= 7:
        return "days_1_7"
    if overdue_days <= 30:
        return "days_8_30"
    if overdue_days <= 60:
        return "days_31_60"
    return "days_61_plus"


def collection_attention(
    collection_status_value: str,
    due_date: date,
    today: date,
    priority: str,
    promise_status: str,
    follow_up_status: str,
    assigned_user_id: uuid.UUID | None,
) -> tuple[int, str, str]:
    if collection_status_value in {"paid", "cancelled"}:
        return 0, "routine", "Nenhuma ação pendente"
    overdue_days = max(0, (today - due_date).days)
    score = min(overdue_days, 100)
    score += {"urgent": 40, "high": 25, "normal": 10, "low": 0}.get(priority, 10)
    if collection_status_value == "due_soon":
        score += 10
    if promise_status == "overdue":
        score += 25
    if follow_up_status == "overdue":
        score += 20
    if assigned_user_id is None:
        score += 10
    level = "critical" if score >= 60 else "attention" if score >= 25 else "routine"
    if promise_status == "overdue":
        action = "Retomar promessa vencida"
    elif follow_up_status == "overdue":
        action = "Realizar acompanhamento atrasado"
    elif overdue_days > 60:
        action = "Avaliar estratégia jurídica"
    elif overdue_days > 30:
        action = "Revisar proposta de acordo"
    elif overdue_days > 7:
        action = "Reforçar negociação"
    elif overdue_days > 0:
        action = "Realizar contato de cobrança"
    elif collection_status_value == "due_soon":
        action = "Lembrar próximo vencimento"
    else:
        action = "Acompanhar vencimento"
    return score, level, action


def collection_report_data(
    db: Session,
    organization_id: uuid.UUID,
    date_from: date,
    date_to: date,
) -> CollectionReportRead:
    if date_from > date_to:
        raise HTTPException(status_code=422, detail="A data inicial não pode ser posterior à data final")
    if (date_to - date_from).days > 731:
        raise HTTPException(status_code=422, detail="O período máximo do relatório é de 24 meses")

    start_at = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end_at = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
    installments = list(db.scalars(
        select(PaymentInstallment).where(PaymentInstallment.organization_id == organization_id)
    ))
    due_items = [
        item for item in installments
        if date_from <= item.due_date <= date_to and item.status != "cancelled"
    ]
    received_items = [
        item for item in installments
        if item.status == "paid" and item.paid_at and start_at <= item.paid_at < end_at
    ]
    today = date.today()
    overdue_items = [
        item for item in installments
        if item.status not in {"paid", "cancelled"} and item.due_date < today
    ]

    actions = list(db.scalars(
        select(CollectionAction)
        .where(
            CollectionAction.organization_id == organization_id,
            CollectionAction.cancelled_at.is_(None),
            CollectionAction.contacted_at >= start_at,
            CollectionAction.contacted_at < end_at,
        )
        .order_by(CollectionAction.contacted_at.desc(), CollectionAction.created_at.desc())
    ))
    user_ids = {action.created_by_user_id for action in actions}
    names = dict(db.execute(
        select(User.id, User.full_name).where(
            User.organization_id == organization_id,
            User.id.in_(user_ids),
        )
    ).all()) if user_ids else {}

    latest_promises: dict[uuid.UUID, CollectionAction] = {}
    for action in actions:
        if action.outcome == "promise_to_pay" and action.promise_date:
            latest_promises.setdefault(action.installment_id, action)

    team_rows: list[CollectionTeamPerformanceRead] = []
    for user_id in sorted(user_ids, key=lambda value: names.get(value, "").casefold()):
        user_actions = [action for action in actions if action.created_by_user_id == user_id]
        user_promises: dict[uuid.UUID, CollectionAction] = {}
        for action in user_actions:
            if action.outcome == "promise_to_pay" and action.promise_date:
                user_promises.setdefault(action.installment_id, action)
        team_rows.append(CollectionTeamPerformanceRead(
            user_id=user_id,
            user_name=names.get(user_id, "Equipe"),
            action_count=len(user_actions),
            contacted_clients=len({action.client_id for action in user_actions}),
            promise_count=len(user_promises),
            promise_amount=sum((Decimal(action.promise_amount or 0) for action in user_promises.values()), Decimal("0")),
            follow_up_count=sum(1 for action in user_actions if action.next_follow_up_at),
        ))

    due_amount = sum((Decimal(item.amount or 0) for item in due_items), Decimal("0"))
    received_amount = sum((Decimal(item.paid_amount or 0) for item in received_items), Decimal("0"))
    recovery_rate = (
        (received_amount / due_amount * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
        if due_amount > 0 else Decimal("0")
    )
    return CollectionReportRead(
        date_from=date_from,
        date_to=date_to,
        due_count=len(due_items),
        due_amount=due_amount,
        received_count=len(received_items),
        received_amount=received_amount,
        overdue_count=len(overdue_items),
        overdue_amount=sum((Decimal(item.amount or 0) for item in overdue_items), Decimal("0")),
        action_count=len(actions),
        contacted_clients=len({action.client_id for action in actions}),
        promise_count=len(latest_promises),
        promise_amount=sum((Decimal(action.promise_amount or 0) for action in latest_promises.values()), Decimal("0")),
        recovery_rate=recovery_rate,
        team=team_rows,
    )


def executive_overview_data(
    db: Session,
    organization_id: uuid.UUID,
    date_from: date,
    date_to: date,
) -> ExecutiveOverviewRead:
    if date_from > date_to:
        raise HTTPException(status_code=422, detail="A data inicial não pode ser posterior à data final")
    if (date_to - date_from).days > 365:
        raise HTTPException(status_code=422, detail="O período máximo da Central Gerencial é de 366 dias")

    period_days = (date_to - date_from).days + 1
    previous_date_to = date_from - timedelta(days=1)
    previous_date_from = previous_date_to - timedelta(days=period_days - 1)
    start_at = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end_at = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
    previous_start_at = datetime.combine(previous_date_from, time.min, tzinfo=timezone.utc)
    previous_end_at = start_at

    clients = list(db.scalars(select(Client).where(Client.organization_id == organization_id)))
    opportunities = list(db.scalars(select(CRMOpportunity).where(CRMOpportunity.organization_id == organization_id)))
    tasks = list(db.scalars(select(CRMTask).where(CRMTask.organization_id == organization_id)))
    interactions_all = list(db.scalars(select(CRMInteraction).where(
        CRMInteraction.organization_id == organization_id,
        CRMInteraction.occurred_at >= previous_start_at,
        CRMInteraction.occurred_at < end_at,
    )))
    installments = list(db.scalars(select(PaymentInstallment).where(PaymentInstallment.organization_id == organization_id)))
    actions_all = list(db.scalars(select(CollectionAction).where(
        CollectionAction.organization_id == organization_id,
        CollectionAction.cancelled_at.is_(None),
        CollectionAction.contacted_at >= previous_start_at,
        CollectionAction.contacted_at < end_at,
    )))
    users = list(db.scalars(select(User).where(
        User.organization_id == organization_id,
        User.deleted_at.is_(None),
        User.status == "active",
    ).order_by(User.full_name)))

    def as_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    in_current = lambda value: bool(value and start_at <= as_utc(value) < end_at)
    in_previous = lambda value: bool(value and previous_start_at <= as_utc(value) < previous_end_at)
    new_clients = [item for item in clients if in_current(item.created_at)]
    previous_new_clients = [item for item in clients if in_previous(item.created_at)]
    interactions = [item for item in interactions_all if in_current(item.occurred_at)]
    previous_interactions = [item for item in interactions_all if in_previous(item.occurred_at)]
    completed_tasks = [item for item in tasks if item.status == "completed" and in_current(item.completed_at)]
    previous_completed_tasks = [item for item in tasks if item.status == "completed" and in_previous(item.completed_at)]
    received = [item for item in installments if item.status == "paid" and in_current(item.paid_at)]
    previous_received = [item for item in installments if item.status == "paid" and in_previous(item.paid_at)]
    collection_actions = [item for item in actions_all if in_current(item.contacted_at)]
    previous_collection_actions = [item for item in actions_all if in_previous(item.contacted_at)]

    open_stages = {"lead", "qualified", "proposal", "negotiation"}
    open_opportunities = [item for item in opportunities if item.stage in open_stages]
    won = [item for item in opportunities if item.stage == "won" and in_current(item.updated_at)]
    lost = [item for item in opportunities if item.stage == "lost" and in_current(item.updated_at)]
    decided = len(won) + len(lost)
    conversion_rate = (
        (Decimal(len(won)) / Decimal(decided) * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
        if decided else Decimal("0")
    )
    today = date.today()
    due_items = [item for item in installments if date_from <= item.due_date <= date_to and item.status != "cancelled"]
    overdue_items = [item for item in installments if item.status not in {"paid", "cancelled"} and item.due_date < today]
    due_amount = sum((Decimal(item.amount or 0) for item in due_items), Decimal("0"))
    received_amount = sum((Decimal(item.paid_amount or 0) for item in received), Decimal("0"))
    previous_received_amount = sum((Decimal(item.paid_amount or 0) for item in previous_received), Decimal("0"))
    recovery_rate = (
        (received_amount / due_amount * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
        if due_amount else Decimal("0")
    )

    trend: list[ExecutiveTrendPointRead] = []
    for offset in range(period_days):
        day = date_from + timedelta(days=offset)
        trend.append(ExecutiveTrendPointRead(
            day=day,
            new_clients=sum(1 for item in new_clients if item.created_at.date() == day),
            interactions=sum(1 for item in interactions if item.occurred_at.date() == day),
            completed_tasks=sum(1 for item in completed_tasks if item.completed_at.date() == day),
            received_amount=sum((Decimal(item.paid_amount or 0) for item in received if item.paid_at.date() == day), Decimal("0")),
        ))

    stage_order = ["lead", "qualified", "proposal", "negotiation", "won", "lost"]
    pipeline = [ExecutivePipelineStageRead(
        stage=stage,
        count=sum(1 for item in opportunities if item.stage == stage),
        amount=sum((Decimal(str(item.estimated_value or 0)) for item in opportunities if item.stage == stage), Decimal("0")),
    ) for stage in stage_order]

    team = [ExecutiveTeamPerformanceRead(
        user_id=user.id,
        user_name=user.full_name,
        assigned_clients=sum(1 for item in clients if item.assigned_user_id == user.id),
        open_opportunities=sum(1 for item in open_opportunities if item.owner_id == user.id),
        pending_tasks=sum(1 for item in tasks if item.assigned_to_id == user.id and item.status in {"pending", "in_progress"}),
        completed_tasks=sum(1 for item in completed_tasks if item.assigned_to_id == user.id),
        interactions=sum(1 for item in interactions if item.user_id == user.id),
        collection_actions=sum(1 for item in collection_actions if item.created_by_user_id == user.id),
    ) for user in users]

    return ExecutiveOverviewRead(
        date_from=date_from,
        date_to=date_to,
        previous_date_from=previous_date_from,
        previous_date_to=previous_date_to,
        total_clients=len(clients),
        new_clients=len(new_clients),
        previous_new_clients=len(previous_new_clients),
        interactions=len(interactions),
        previous_interactions=len(previous_interactions),
        completed_tasks=len(completed_tasks),
        previous_completed_tasks=len(previous_completed_tasks),
        received_amount=received_amount,
        previous_received_amount=previous_received_amount,
        collection_actions=len(collection_actions),
        previous_collection_actions=len(previous_collection_actions),
        open_pipeline_count=len(open_opportunities),
        open_pipeline_value=sum((Decimal(str(item.estimated_value or 0)) for item in open_opportunities), Decimal("0")),
        weighted_pipeline_value=sum((Decimal(str(item.estimated_value or 0)) * Decimal(item.probability or 0) / Decimal("100") for item in open_opportunities), Decimal("0")),
        won_count=len(won),
        lost_count=len(lost),
        conversion_rate=conversion_rate,
        due_amount=due_amount,
        recovery_rate=recovery_rate,
        pending_tasks=sum(1 for item in tasks if item.status in {"pending", "in_progress"}),
        overdue_tasks=sum(1 for item in tasks if item.status in {"pending", "in_progress"} and item.due_at and as_utc(item.due_at) < datetime.now(timezone.utc)),
        overdue_collections=len(overdue_items),
        overdue_amount=sum((Decimal(item.amount or 0) for item in overdue_items), Decimal("0")),
        trend=trend,
        pipeline=pipeline,
        team=team,
    )


@router.get("/executive-overview", response_model=ExecutiveOverviewRead)
def executive_overview(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions("report.read")),
):
    today = date.today()
    return executive_overview_data(db, identity.organization_id, date_from or today - timedelta(days=29), date_to or today)


@router.get("/executive-overview.csv")
def export_executive_overview(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    identity: IdentityContext = Depends(require_permissions("report.read", "report.export")),
):
    today = date.today()
    report = executive_overview_data(db, identity.organization_id, date_from or today - timedelta(days=29), date_to or today)
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["Central Gerencial", "CS Platform", "v5.25.0"])
    writer.writerow(["Período", report.date_from.strftime("%d/%m/%Y"), report.date_to.strftime("%d/%m/%Y")])
    writer.writerow([])
    writer.writerow(["Indicador", "Período atual", "Período anterior"])
    writer.writerow(["Novos clientes", report.new_clients, report.previous_new_clients])
    writer.writerow(["Atendimentos", report.interactions, report.previous_interactions])
    writer.writerow(["Tarefas concluídas", report.completed_tasks, report.previous_completed_tasks])
    writer.writerow(["Recebimentos", f"{report.received_amount:.2f}", f"{report.previous_received_amount:.2f}"])
    writer.writerow(["Ações de cobrança", report.collection_actions, report.previous_collection_actions])
    writer.writerow(["Conversão comercial", f"{report.conversion_rate:.2f}%", ""])
    writer.writerow(["Índice de recebimento", f"{report.recovery_rate:.2f}%", ""])
    writer.writerow([])
    writer.writerow(["Etapa do funil", "Quantidade", "Valor"])
    for row in report.pipeline:
        writer.writerow([row.stage, row.count, f"{row.amount:.2f}"])
    writer.writerow([])
    writer.writerow(["Responsável", "Clientes", "Oportunidades", "Tarefas pendentes", "Tarefas concluídas", "Atendimentos", "Ações de cobrança"])
    for row in report.team:
        writer.writerow([row.user_name, row.assigned_clients, row.open_opportunities, row.pending_tasks, row.completed_tasks, row.interactions, row.collection_actions])
    record_audit(
        db,
        organization_id=identity.organization_id,
        user_id=identity.user_id,
        entity_type="management_report",
        entity_id=None,
        action="export",
        new_values={"date_from": str(report.date_from), "date_to": str(report.date_to)},
    )
    db.commit()
    filename = f"central_gerencial_{report.date_from}_{report.date_to}.csv"
    return Response(
        content=("\ufeff" + stream.getvalue()).encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"},
    )


@router.get("/collections/report", response_model=CollectionReportRead)
def collection_report(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    today = date.today()
    return collection_report_data(
        db,
        actor.organization_id,
        date_from or today.replace(day=1),
        date_to or today,
    )


@router.get("/collections/report.csv")
def export_collection_report(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    today = date.today()
    report = collection_report_data(
        db,
        actor.organization_id,
        date_from or today.replace(day=1),
        date_to or today,
    )
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["Relatório gerencial de cobranças"])
    writer.writerow(["Período", report.date_from.strftime("%d/%m/%Y"), report.date_to.strftime("%d/%m/%Y")])
    writer.writerow([])
    writer.writerow(["Indicador", "Quantidade", "Valor"])
    writer.writerow(["Vencimentos no período", report.due_count, f"{report.due_amount:.2f}"])
    writer.writerow(["Recebimentos no período", report.received_count, f"{report.received_amount:.2f}"])
    writer.writerow(["Parcelas atualmente atrasadas", report.overdue_count, f"{report.overdue_amount:.2f}"])
    writer.writerow(["Promessas registradas", report.promise_count, f"{report.promise_amount:.2f}"])
    writer.writerow(["Ações de cobrança", report.action_count, ""])
    writer.writerow(["Clientes contatados", report.contacted_clients, ""])
    writer.writerow(["Índice de recebimento", "", f"{report.recovery_rate:.2f}%"])
    writer.writerow([])
    writer.writerow(["Responsável", "Ações", "Clientes", "Promessas", "Valor prometido", "Acompanhamentos"])
    for row in report.team:
        writer.writerow([
            row.user_name,
            row.action_count,
            row.contacted_clients,
            row.promise_count,
            f"{row.promise_amount:.2f}",
            row.follow_up_count,
        ])
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="collection_action",
        entity_id=None,
        action="export",
        new_values={"date_from": str(report.date_from), "date_to": str(report.date_to)},
    )
    db.commit()
    filename = f"relatorio_cobrancas_{report.date_from}_{report.date_to}.csv"
    return Response(
        content=("\ufeff" + stream.getvalue()).encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/collections", response_model=CollectionsRead)
def list_collections(
    q: str = Query(default="", max_length=200),
    collection_status_filter: str = Query(default="all", alias="status"),
    follow_up_filter: str = Query(default="all"),
    promise_filter: str = Query(default="all"),
    responsible_filter: str = Query(default="all"),
    priority_filter: str = Query(default="all"),
    aging_filter: str = Query(default="all"),
    attention_filter: str = Query(default="all"),
    sort_order: str = Query(default="recommended"),
    due_from: date | None = None,
    due_to: date | None = None,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    if due_from and due_to and due_from > due_to:
        raise HTTPException(status_code=422, detail="A data inicial não pode ser posterior à data final")
    allowed_statuses = {"all", "pending", "due_soon", "paid", "overdue", "cancelled"}
    if collection_status_filter not in allowed_statuses:
        raise HTTPException(status_code=422, detail="Situação de cobrança inválida")
    allowed_tracking_filters = {"all", "overdue", "today", "upcoming", "none"}
    if follow_up_filter not in allowed_tracking_filters:
        raise HTTPException(status_code=422, detail="Filtro de acompanhamento inválido")
    if promise_filter not in allowed_tracking_filters:
        raise HTTPException(status_code=422, detail="Filtro de promessa inválido")
    allowed_priorities = {"all", "low", "normal", "high", "urgent"}
    if priority_filter not in allowed_priorities:
        raise HTTPException(status_code=422, detail="Prioridade de cobrança inválida")
    allowed_aging_filters = {"all", "days_1_7", "days_8_30", "days_31_60", "days_61_plus"}
    if aging_filter not in allowed_aging_filters:
        raise HTTPException(status_code=422, detail="Faixa de atraso inválida")
    if attention_filter not in {"all", "critical", "attention", "routine"}:
        raise HTTPException(status_code=422, detail="Nível de atenção inválido")
    if sort_order not in {"recommended", "due_date", "amount_desc"}:
        raise HTTPException(status_code=422, detail="Ordenação da fila inválida")
    responsible_id: uuid.UUID | None = None
    if responsible_filter not in {"all", "mine", "unassigned"}:
        try:
            responsible_id = uuid.UUID(responsible_filter)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Responsável pela cobrança inválido") from exc
        responsible_exists = db.scalar(select(User.id).where(
            User.id == responsible_id,
            User.organization_id == actor.organization_id,
            User.deleted_at.is_(None),
        ))
        if not responsible_exists:
            raise HTTPException(status_code=422, detail="Responsável pela cobrança não pertence à organização")

    rows = db.execute(
        select(PaymentInstallment, PaymentAgreement, Client)
        .join(PaymentAgreement, PaymentAgreement.id == PaymentInstallment.agreement_id)
        .join(Client, Client.id == PaymentInstallment.client_id)
        .where(PaymentInstallment.organization_id == actor.organization_id)
        .order_by(PaymentInstallment.due_date, Client.full_name, PaymentInstallment.installment_number)
    ).all()
    queue_users = list(db.scalars(select(User).where(
        User.organization_id == actor.organization_id,
        User.deleted_at.is_(None),
        User.status == "active",
    ).order_by(User.full_name, User.id)))
    assigned_names = {user.id: user.full_name for user in queue_users}
    action_rows = list(db.scalars(
        select(CollectionAction)
        .where(CollectionAction.organization_id == actor.organization_id)
        .order_by(CollectionAction.contacted_at.desc(), CollectionAction.created_at.desc())
    ))
    action_counts: dict[uuid.UUID, int] = {}
    latest_actions: dict[uuid.UUID, CollectionAction] = {}
    latest_promises: dict[uuid.UUID, CollectionAction] = {}
    for action in action_rows:
        if action.cancelled_at:
            continue
        action_counts[action.installment_id] = action_counts.get(action.installment_id, 0) + 1
        latest_actions.setdefault(action.installment_id, action)
        if action.outcome == "promise_to_pay" and action.promise_date:
            latest_promises.setdefault(action.installment_id, action)
    today = date.today()
    month_start = today.replace(day=1)
    normalized_query = q.strip().casefold()
    status_changed = False
    all_items: list[CollectionItemRead] = []

    for installment, agreement, client in rows:
        effective_status = collection_status(installment, today)
        stored_status = effective_status if effective_status != "due_soon" else "pending"
        if installment.status not in {"paid", "cancelled"} and installment.status != stored_status:
            installment.status = stored_status
            status_changed = True
        latest_action = latest_actions.get(installment.id)
        latest_promise = latest_promises.get(installment.id)
        follow_up_status = "none"
        if latest_action and latest_action.next_follow_up_at:
            follow_up_date = latest_action.next_follow_up_at.date()
            follow_up_status = "overdue" if follow_up_date < today else "today" if follow_up_date == today else "upcoming"
        promise_status = "none"
        if latest_promise and effective_status in {"pending", "due_soon", "overdue"}:
            promise_status = "overdue" if latest_promise.promise_date < today else "today" if latest_promise.promise_date == today else "upcoming"
        priority = installment.collection_priority or "normal"
        attention_score, attention_level, recommended_action = collection_attention(
            effective_status,
            installment.due_date,
            today,
            priority,
            promise_status,
            follow_up_status,
            installment.collection_assigned_user_id,
        )
        all_items.append(CollectionItemRead(
            id=installment.id,
            client_id=client.id,
            client_name=client.full_name,
            agreement_id=agreement.id,
            agreement_title=agreement.title,
            installment_number=installment.installment_number,
            due_date=installment.due_date,
            amount=installment.amount,
            status=effective_status,
            paid_amount=installment.paid_amount,
            paid_at=installment.paid_at,
            payment_method=installment.payment_method,
            action_count=action_counts.get(installment.id, 0),
            last_contacted_at=latest_action.contacted_at if latest_action else None,
            next_follow_up_at=latest_action.next_follow_up_at if latest_action else None,
            latest_outcome=latest_action.outcome if latest_action else None,
            follow_up_status=follow_up_status,
            latest_promise_date=latest_promise.promise_date if latest_promise else None,
            latest_promise_amount=latest_promise.promise_amount if latest_promise else None,
            promise_status=promise_status,
            assigned_user_id=installment.collection_assigned_user_id,
            assigned_user_name=assigned_names.get(installment.collection_assigned_user_id),
            priority=priority,
            overdue_days=max(0, (today - installment.due_date).days) if effective_status == "overdue" else 0,
            attention_score=attention_score,
            attention_level=attention_level,
            recommended_action=recommended_action,
        ))
    if status_changed:
        db.commit()

    open_items = [item for item in all_items if item.status in {"pending", "due_soon", "overdue"}]
    overdue_items = [item for item in all_items if item.status == "overdue"]
    due_soon_items = [item for item in all_items if item.status == "due_soon"]
    paid_this_month = [
        item for item in all_items
        if item.status == "paid" and item.paid_at and item.paid_at.date() >= month_start
    ]
    open_ids = {item.id for item in open_items}
    follow_up_today_count = 0
    overdue_follow_up_count = 0
    upcoming_follow_up_count = 0
    for installment_id, action in latest_actions.items():
        if installment_id not in open_ids or not action.next_follow_up_at:
            continue
        follow_up_date = action.next_follow_up_at.date()
        if follow_up_date == today:
            follow_up_today_count += 1
        elif follow_up_date < today:
            overdue_follow_up_count += 1
        else:
            upcoming_follow_up_count += 1
    open_promises = [item for item in open_items if item.promise_status != "none"]
    overdue_promises = [item for item in open_promises if item.promise_status == "overdue"]
    workload: list[CollectionWorkloadRead] = []
    for user in queue_users:
        user_items = [item for item in open_items if item.assigned_user_id == user.id]
        workload.append(CollectionWorkloadRead(
            user_id=user.id,
            user_name=user.full_name,
            open_count=len(user_items),
            overdue_count=sum(1 for item in user_items if item.status == "overdue"),
            urgent_count=sum(1 for item in user_items if item.priority == "urgent"),
            open_amount=sum((item.amount for item in user_items), Decimal("0")),
        ))
    unassigned_items = [item for item in open_items if item.assigned_user_id is None]
    if unassigned_items:
        workload.append(CollectionWorkloadRead(
            user_id=None,
            user_name="Sem responsável",
            open_count=len(unassigned_items),
            overdue_count=sum(1 for item in unassigned_items if item.status == "overdue"),
            urgent_count=sum(1 for item in unassigned_items if item.priority == "urgent"),
            open_amount=sum((item.amount for item in unassigned_items), Decimal("0")),
        ))
    workload.sort(key=lambda row: (-row.urgent_count, -row.overdue_count, -row.open_count, row.user_name.casefold()))
    aging_definitions = (
        ("days_1_7", "1 a 7 dias"),
        ("days_8_30", "8 a 30 dias"),
        ("days_31_60", "31 a 60 dias"),
        ("days_61_plus", "Mais de 60 dias"),
    )
    aging = [CollectionAgingRead(
        bucket=bucket,
        label=label,
        count=sum(1 for item in overdue_items if collection_aging_bucket(item.due_date, today) == bucket),
        amount=sum((item.amount for item in overdue_items if collection_aging_bucket(item.due_date, today) == bucket), Decimal("0")),
    ) for bucket, label in aging_definitions]
    summary = CollectionSummaryRead(
        open_count=len(open_items),
        open_amount=sum((item.amount for item in open_items), Decimal("0")),
        overdue_count=len(overdue_items),
        overdue_amount=sum((item.amount for item in overdue_items), Decimal("0")),
        due_soon_count=len(due_soon_items),
        due_soon_amount=sum((item.amount for item in due_soon_items), Decimal("0")),
        paid_this_month_count=len(paid_this_month),
        paid_this_month_amount=sum((item.paid_amount for item in paid_this_month), Decimal("0")),
        follow_up_today_count=follow_up_today_count,
        overdue_follow_up_count=overdue_follow_up_count,
        upcoming_follow_up_count=upcoming_follow_up_count,
        open_promises_count=len(open_promises),
        overdue_promises_count=len(overdue_promises),
        urgent_count=sum(1 for item in open_items if item.priority == "urgent"),
        unassigned_count=sum(1 for item in open_items if item.assigned_user_id is None),
        critical_count=sum(1 for item in open_items if item.attention_level == "critical"),
        attention_count=sum(1 for item in open_items if item.attention_level == "attention"),
    )

    items = all_items
    if normalized_query:
        items = [
            item for item in items
            if normalized_query in item.client_name.casefold()
            or normalized_query in item.agreement_title.casefold()
        ]
    if collection_status_filter != "all":
        items = [item for item in items if item.status == collection_status_filter]
    if due_from:
        items = [item for item in items if item.due_date >= due_from]
    if due_to:
        items = [item for item in items if item.due_date <= due_to]
    if follow_up_filter != "all":
        items = [item for item in items if item.follow_up_status == follow_up_filter]
    if promise_filter != "all":
        items = [item for item in items if item.promise_status == promise_filter]
    if responsible_filter == "mine":
        items = [item for item in items if item.assigned_user_id == actor.id]
    elif responsible_filter == "unassigned":
        items = [item for item in items if item.assigned_user_id is None]
    elif responsible_id:
        items = [item for item in items if item.assigned_user_id == responsible_id]
    if priority_filter != "all":
        items = [item for item in items if item.priority == priority_filter]
    if aging_filter != "all":
        items = [item for item in items if item.status == "overdue" and collection_aging_bucket(item.due_date, today) == aging_filter]
    if attention_filter != "all":
        items = [item for item in items if item.attention_level == attention_filter]
    if sort_order == "recommended":
        items.sort(key=lambda item: (
            item.status in {"paid", "cancelled"},
            -item.attention_score,
            item.due_date,
            item.client_name.casefold(),
        ))
    elif sort_order == "amount_desc":
        items.sort(key=lambda item: (-item.amount, item.due_date, item.client_name.casefold()))
    else:
        items.sort(key=lambda item: (item.due_date, item.client_name.casefold()))

    return CollectionsRead(summary=summary, workload=workload, aging=aging, items=items, total=len(items))


@router.get("/operational-alerts", response_model=OperationalAlertsRead)
def list_operational_alerts(
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    collections = list_collections(
        q="",
        collection_status_filter="all",
        follow_up_filter="all",
        promise_filter="all",
        responsible_filter="all",
        priority_filter="all",
        aging_filter="all",
        attention_filter="all",
        sort_order="recommended",
        due_from=None,
        due_to=None,
        db=db,
        actor=actor,
    )
    now = datetime.now(timezone.utc)
    overdue_tasks = 0
    for task in db.scalars(select(CRMTask).where(
        CRMTask.organization_id == actor.organization_id,
        CRMTask.status.in_({"pending", "in_progress"}),
        CRMTask.due_at.is_not(None),
    )):
        due_at = task.due_at
        if due_at and due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        if due_at and due_at < now:
            overdue_tasks += 1

    definitions = (
        (
            "critical_collections", "critical", "Cobranças críticas",
            "Cobranças que precisam de ação prioritária.",
            collections.summary.critical_count, "collections", "attention:critical",
        ),
        (
            "overdue_promises", "critical", "Promessas vencidas",
            "Promessas de pagamento que venceram sem baixa.",
            collections.summary.overdue_promises_count, "collections", "promise:overdue",
        ),
        (
            "overdue_follow_ups", "warning", "Acompanhamentos atrasados",
            "Retornos de cobrança que já passaram da data.",
            collections.summary.overdue_follow_up_count, "collections", "follow_up:overdue",
        ),
        (
            "overdue_tasks", "critical", "Tarefas do CRM atrasadas",
            "Tarefas pendentes com prazo vencido.",
            overdue_tasks, "crm", "task:overdue",
        ),
    )
    items = [OperationalAlertRead(
        key=key,
        severity=severity,
        title=title,
        detail=detail,
        count=count,
        target_view=target_view,
        target_filter=target_filter,
    ) for key, severity, title, detail, count, target_view, target_filter in definitions if count]
    return OperationalAlertsRead(
        total=sum(item.count for item in items),
        critical_count=sum(item.count for item in items if item.severity == "critical"),
        items=items,
    )


@router.get("/operational-agenda", response_model=OperationalAgendaRead)
def list_operational_agenda(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    today = date.today()
    date_from = date_from or today - timedelta(days=30)
    date_to = date_to or today + timedelta(days=30)
    if date_from > date_to:
        raise HTTPException(status_code=422, detail="A data inicial não pode ser posterior à data final")
    if (date_to - date_from).days > 366:
        raise HTTPException(status_code=422, detail="O período máximo da agenda é de 12 meses")

    collections = list_collections(
        q="", collection_status_filter="all", follow_up_filter="all", promise_filter="all",
        responsible_filter="all", priority_filter="all", aging_filter="all", attention_filter="all",
        sort_order="recommended", due_from=None, due_to=None, db=db, actor=actor,
    )
    items: list[OperationalAgendaItemRead] = []

    def agenda_status(value: date) -> str:
        return "overdue" if value < today else "today" if value == today else "upcoming"

    for collection in collections.items:
        if collection.status not in {"pending", "due_soon", "overdue"}:
            continue
        if collection.next_follow_up_at and date_from <= collection.next_follow_up_at.date() <= date_to:
            items.append(OperationalAgendaItemRead(
                id=f"follow-up:{collection.id}", kind="follow_up", title="Acompanhamento de cobrança",
                client_id=collection.client_id, client_name=collection.client_name,
                due_at=collection.next_follow_up_at, status=agenda_status(collection.next_follow_up_at.date()),
                priority=collection.priority, assigned_user_id=collection.assigned_user_id,
                assigned_user_name=collection.assigned_user_name,
                target_filter=f"follow_up:{collection.follow_up_status}",
            ))
        if collection.latest_promise_date and date_from <= collection.latest_promise_date <= date_to:
            items.append(OperationalAgendaItemRead(
                id=f"promise:{collection.id}", kind="promise", title="Promessa de pagamento",
                client_id=collection.client_id, client_name=collection.client_name,
                due_at=datetime.combine(collection.latest_promise_date, time(12), tzinfo=timezone.utc),
                status=agenda_status(collection.latest_promise_date), priority=collection.priority,
                assigned_user_id=collection.assigned_user_id, assigned_user_name=collection.assigned_user_name,
                target_filter=f"promise:{collection.promise_status}",
            ))

    client_names = dict(db.execute(select(Client.id, Client.full_name).where(
        Client.organization_id == actor.organization_id,
    )).all())
    agenda_users = list(db.scalars(select(User).where(
        User.organization_id == actor.organization_id,
        User.deleted_at.is_(None), User.status == "active",
    ).order_by(User.full_name, User.id)))
    user_names = {user.id: user.full_name for user in agenda_users}
    for task in db.scalars(select(CRMTask).where(
        CRMTask.organization_id == actor.organization_id,
        CRMTask.status.in_({"pending", "in_progress"}),
        CRMTask.due_at.is_not(None),
    )):
        due_at = task.due_at
        if due_at and due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        if due_at and date_from <= due_at.date() <= date_to:
            items.append(OperationalAgendaItemRead(
                id=f"task:{task.id}", kind="task", title=task.title, client_id=task.client_id,
                client_name=client_names.get(task.client_id), due_at=due_at,
                status=agenda_status(due_at.date()), priority=task.priority or "normal",
                assigned_user_id=task.assigned_to_id, assigned_user_name=user_names.get(task.assigned_to_id),
                target_filter="task:overdue" if due_at.date() < today else "task:all",
            ))
    status_order = {"overdue": 0, "today": 1, "upcoming": 2}
    priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    items.sort(key=lambda item: (status_order[item.status], item.due_at, priority_order[item.priority], item.title.casefold()))
    workload = []
    for user in agenda_users:
        user_items = [item for item in items if item.assigned_user_id == user.id]
        workload.append(OperationalAgendaWorkloadRead(
            user_id=user.id, user_name=user.full_name, total=len(user_items),
            overdue=sum(item.status == "overdue" for item in user_items),
            today=sum(item.status == "today" for item in user_items),
            upcoming=sum(item.status == "upcoming" for item in user_items),
        ))
    unassigned_items = [item for item in items if item.assigned_user_id is None]
    if unassigned_items:
        workload.append(OperationalAgendaWorkloadRead(
            user_id=None, user_name="Sem responsável", total=len(unassigned_items),
            overdue=sum(item.status == "overdue" for item in unassigned_items),
            today=sum(item.status == "today" for item in unassigned_items),
            upcoming=sum(item.status == "upcoming" for item in unassigned_items),
        ))
    workload.sort(key=lambda row: (-row.overdue, -row.today, -row.total, row.user_name.casefold()))
    return OperationalAgendaRead(
        date_from=date_from, date_to=date_to,
        summary=OperationalAgendaSummaryRead(
            total=len(items), overdue=sum(item.status == "overdue" for item in items),
            today=sum(item.status == "today" for item in items),
            upcoming=sum(item.status == "upcoming" for item in items),
        ), workload=workload, items=items,
    )


@router.get("/operational-agenda.csv")
def export_operational_agenda_csv(
    date_from: date | None = None,
    date_to: date | None = None,
    kind: str = Query(default="all"),
    agenda_status: str = Query(default="all", alias="status"),
    responsible: str = Query(default="all"),
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    if kind not in {"all", "task", "follow_up", "promise"}:
        raise HTTPException(status_code=422, detail="Tipo de compromisso inválido")
    if agenda_status not in {"all", "overdue", "today", "upcoming"}:
        raise HTTPException(status_code=422, detail="Situação da agenda inválida")
    agenda = list_operational_agenda(date_from=date_from, date_to=date_to, db=db, actor=actor)
    items = agenda.items
    if kind != "all":
        items = [item for item in items if item.kind == kind]
    if agenda_status != "all":
        items = [item for item in items if item.status == agenda_status]
    if responsible == "mine":
        items = [item for item in items if item.assigned_user_id == actor.id]
    elif responsible == "unassigned":
        items = [item for item in items if item.assigned_user_id is None]
    elif responsible != "all":
        try:
            responsible_id = uuid.UUID(responsible)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Responsável inválido") from exc
        items = [item for item in items if item.assigned_user_id == responsible_id]

    labels = {
        "task": "Tarefa do CRM", "follow_up": "Acompanhamento", "promise": "Promessa",
        "overdue": "Atrasado", "today": "Para hoje", "upcoming": "Próximo",
        "low": "Baixa", "normal": "Normal", "high": "Alta", "urgent": "Urgente",
    }
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";")
    writer.writerow(["Agenda operacional", "CS Platform", "v5.25.0"])
    writer.writerow(["Período", agenda.date_from.strftime("%d/%m/%Y"), agenda.date_to.strftime("%d/%m/%Y")])
    writer.writerow([])
    writer.writerow(["Data e hora", "Tipo", "Situação", "Título", "Cliente", "Responsável", "Prioridade"])
    for item in items:
        writer.writerow([
            item.due_at.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M"), labels.get(item.kind, item.kind),
            labels.get(item.status, item.status), item.title, item.client_name or "—",
            item.assigned_user_name or "Sem responsável", labels.get(item.priority, item.priority),
        ])
    body = ("\ufeff" + stream.getvalue()).encode("utf-8")
    return Response(
        content=body, media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="agenda_operacional.csv"', "Cache-Control": "no-store"},
    )


def owned_collection_installment(
    db: Session, installment_id: uuid.UUID, organization_id: uuid.UUID
) -> PaymentInstallment:
    installment = db.scalar(
        select(PaymentInstallment).where(
            PaymentInstallment.id == installment_id,
            PaymentInstallment.organization_id == organization_id,
        )
    )
    if not installment:
        raise HTTPException(status_code=404, detail="Parcela não encontrada")
    return installment


@router.put("/collections/{installment_id}/assignment", response_model=PaymentInstallmentRead)
def update_collection_assignment(
    installment_id: uuid.UUID,
    payload: CollectionAssignmentUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    if actor.role not in {"admin", "supervisor"} and not actor.is_superuser:
        raise HTTPException(status_code=403, detail="Somente administradores e supervisores podem organizar a fila de cobranças")
    installment = owned_collection_installment(db, installment_id, actor.organization_id)
    assignee = None
    if payload.assigned_user_id:
        assignee = db.scalar(select(User).where(
            User.id == payload.assigned_user_id,
            User.organization_id == actor.organization_id,
            User.deleted_at.is_(None),
            User.status == "active",
        ))
        if not assignee:
            raise HTTPException(status_code=422, detail="O responsável selecionado não está ativo nesta organização")
    old_values = {
        "assigned_user_id": str(installment.collection_assigned_user_id) if installment.collection_assigned_user_id else None,
        "priority": installment.collection_priority,
    }
    installment.collection_assigned_user_id = assignee.id if assignee else None
    installment.collection_priority = payload.priority
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="payment_installment",
        entity_id=installment.id,
        action="update",
        new_values={
            "previous": old_values,
            "assigned_user_id": str(assignee.id) if assignee else None,
            "assigned_user_name": assignee.full_name if assignee else None,
            "priority": installment.collection_priority,
        },
    )
    db.commit()
    db.refresh(installment)
    return installment


@router.put("/collections/assignment/bulk", response_model=CollectionBulkAssignmentResult)
def update_collection_assignments_bulk(
    payload: CollectionBulkAssignmentUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    if actor.role not in {"admin", "supervisor"} and not actor.is_superuser:
        raise HTTPException(status_code=403, detail="Somente administradores e supervisores podem organizar a fila de cobranças")

    requested_ids = set(payload.installment_ids)
    installments = list(db.scalars(select(PaymentInstallment).where(
        PaymentInstallment.id.in_(requested_ids),
        PaymentInstallment.organization_id == actor.organization_id,
    )))
    if len(installments) != len(requested_ids):
        raise HTTPException(status_code=404, detail="Uma ou mais cobranças selecionadas não foram encontradas")

    changes_assignee = "assigned_user_id" in payload.model_fields_set
    assignee = None
    if changes_assignee and payload.assigned_user_id:
        assignee = db.scalar(select(User).where(
            User.id == payload.assigned_user_id,
            User.organization_id == actor.organization_id,
            User.deleted_at.is_(None),
            User.status == "active",
        ))
        if not assignee:
            raise HTTPException(status_code=422, detail="O responsável selecionado não está ativo nesta organização")

    for installment in installments:
        old_values = {
            "assigned_user_id": str(installment.collection_assigned_user_id) if installment.collection_assigned_user_id else None,
            "priority": installment.collection_priority,
        }
        if changes_assignee:
            installment.collection_assigned_user_id = assignee.id if assignee else None
        if payload.priority is not None:
            installment.collection_priority = payload.priority
        audit_values = {"previous": old_values, "bulk_update": True}
        if changes_assignee:
            audit_values.update({
                "assigned_user_id": str(assignee.id) if assignee else None,
                "assigned_user_name": assignee.full_name if assignee else None,
            })
        if payload.priority is not None:
            audit_values["priority"] = installment.collection_priority
        record_audit(
            db,
            organization_id=actor.organization_id,
            user_id=actor.id,
            entity_type="payment_installment",
            entity_id=installment.id,
            action="update",
            new_values=audit_values,
        )

    db.commit()
    return CollectionBulkAssignmentResult(updated_count=len(installments))


@router.put("/collections/distribution/balanced", response_model=CollectionDistributionResult)
def distribute_collections_balanced(
    payload: CollectionDistributionCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    if actor.role not in {"admin", "supervisor"} and not actor.is_superuser:
        raise HTTPException(status_code=403, detail="Somente administradores e supervisores podem distribuir cobranças")

    requested_ids = set(payload.installment_ids)
    installments = list(db.scalars(select(PaymentInstallment).where(
        PaymentInstallment.id.in_(requested_ids),
        PaymentInstallment.organization_id == actor.organization_id,
    )))
    if len(installments) != len(requested_ids):
        raise HTTPException(status_code=404, detail="Uma ou mais cobranças selecionadas não foram encontradas")
    if any(installment.status in {"paid", "cancelled"} for installment in installments):
        raise HTTPException(status_code=422, detail="Cobranças pagas ou canceladas não podem ser distribuídas")

    requested_user_ids = set(payload.user_ids)
    users = list(db.scalars(select(User).where(
        User.id.in_(requested_user_ids),
        User.organization_id == actor.organization_id,
        User.deleted_at.is_(None),
        User.status == "active",
    ).order_by(User.full_name, User.id)))
    if len(users) != len(requested_user_ids):
        raise HTTPException(status_code=422, detail="Um ou mais responsáveis não estão ativos nesta organização")

    baseline_assignments = list(db.scalars(select(PaymentInstallment.collection_assigned_user_id).where(
        PaymentInstallment.organization_id == actor.organization_id,
        PaymentInstallment.status.notin_({"paid", "cancelled"}),
        PaymentInstallment.id.notin_(requested_ids),
        PaymentInstallment.collection_assigned_user_id.in_(requested_user_ids),
    )))
    load = {user.id: baseline_assignments.count(user.id) for user in users}
    distributed = {user.id: 0 for user in users}
    priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    installments.sort(key=lambda item: (
        priority_order.get(item.collection_priority or "normal", 2),
        item.due_date,
        item.installment_number,
        str(item.id),
    ))

    for installment in installments:
        assignee = min(users, key=lambda user: (load[user.id], user.full_name.casefold(), str(user.id)))
        old_values = {
            "assigned_user_id": str(installment.collection_assigned_user_id) if installment.collection_assigned_user_id else None,
            "priority": installment.collection_priority,
        }
        installment.collection_assigned_user_id = assignee.id
        if payload.priority is not None:
            installment.collection_priority = payload.priority
        load[assignee.id] += 1
        distributed[assignee.id] += 1
        record_audit(
            db,
            organization_id=actor.organization_id,
            user_id=actor.id,
            entity_type="payment_installment",
            entity_id=installment.id,
            action="update",
            new_values={
                "previous": old_values,
                "assigned_user_id": str(assignee.id),
                "assigned_user_name": assignee.full_name,
                "priority": installment.collection_priority,
                "balanced_distribution": True,
            },
        )

    db.commit()
    return CollectionDistributionResult(
        updated_count=len(installments),
        distribution=[
            CollectionDistributionUserResult(
                user_id=user.id,
                user_name=user.full_name,
                assigned_count=distributed[user.id],
            )
            for user in users
        ],
    )


def collection_action_read(
    action: CollectionAction, user_name: str, cancelled_by_name: str | None = None
) -> CollectionActionRead:
    return CollectionActionRead(
        id=action.id,
        organization_id=action.organization_id,
        client_id=action.client_id,
        agreement_id=action.agreement_id,
        installment_id=action.installment_id,
        created_by_user_id=action.created_by_user_id,
        created_by_name=user_name,
        action_type=action.action_type,
        outcome=action.outcome,
        contacted_at=action.contacted_at,
        notes=action.notes,
        promise_date=action.promise_date,
        promise_amount=action.promise_amount,
        next_follow_up_at=action.next_follow_up_at,
        created_at=action.created_at,
        cancelled_at=action.cancelled_at,
        cancelled_by_user_id=action.cancelled_by_user_id,
        cancelled_by_name=cancelled_by_name,
        cancellation_reason=action.cancellation_reason,
    )


@router.get("/collections/{installment_id}/actions", response_model=list[CollectionActionRead])
def list_collection_actions(
    installment_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    owned_collection_installment(db, installment_id, actor.organization_id)
    actions = list(db.scalars(
        select(CollectionAction)
        .where(
            CollectionAction.installment_id == installment_id,
            CollectionAction.organization_id == actor.organization_id,
        )
        .order_by(CollectionAction.contacted_at.desc(), CollectionAction.created_at.desc())
    ))
    user_ids = {
        user_id for action in actions
        for user_id in (action.created_by_user_id, action.cancelled_by_user_id)
        if user_id
    }
    names = dict(db.execute(select(User.id, User.full_name).where(User.id.in_(user_ids))).all()) if user_ids else {}
    return [
        collection_action_read(action, names.get(action.created_by_user_id, "Equipe"), names.get(action.cancelled_by_user_id))
        for action in actions
    ]


@router.post(
    "/collections/{installment_id}/actions",
    response_model=CollectionActionRead,
    status_code=201,
)
def add_collection_action(
    installment_id: uuid.UUID,
    payload: CollectionActionCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    installment = owned_collection_installment(db, installment_id, actor.organization_id)
    if installment.status in {"paid", "cancelled"}:
        raise HTTPException(status_code=409, detail="A parcela paga ou cancelada não aceita nova ação de cobrança")
    action = CollectionAction(
        organization_id=actor.organization_id,
        client_id=installment.client_id,
        agreement_id=installment.agreement_id,
        installment_id=installment.id,
        created_by_user_id=actor.id,
        **payload.model_dump(),
    )
    db.add(action)
    db.flush()
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="collection_action",
        entity_id=action.id,
        action="create",
        new_values={
            "installment_id": str(installment.id),
            "action_type": action.action_type,
            "outcome": action.outcome,
            "promise_date": str(action.promise_date) if action.promise_date else None,
            "promise_amount": str(action.promise_amount) if action.promise_amount else None,
            "next_follow_up_at": action.next_follow_up_at.isoformat() if action.next_follow_up_at else None,
        },
    )
    db.commit()
    db.refresh(action)
    return collection_action_read(action, actor.full_name)


@router.post(
    "/collections/actions/{action_id}/cancel",
    response_model=CollectionActionRead,
)
def cancel_collection_action(
    action_id: uuid.UUID,
    payload: CollectionActionCancel,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    if actor.role != "admin" and not actor.is_superuser:
        raise HTTPException(status_code=403, detail="Somente administradores podem anular ações de cobrança")
    action = db.scalar(
        select(CollectionAction).where(
            CollectionAction.id == action_id,
            CollectionAction.organization_id == actor.organization_id,
        )
    )
    if not action:
        raise HTTPException(status_code=404, detail="Ação de cobrança não encontrada")
    if action.cancelled_at:
        raise HTTPException(status_code=409, detail="Esta ação de cobrança já foi anulada")
    action.cancelled_at = datetime.now(timezone.utc)
    action.cancelled_by_user_id = actor.id
    action.cancellation_reason = payload.reason.strip()
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="collection_action",
        entity_id=action.id,
        action="cancel",
        new_values={"reason": action.cancellation_reason, "installment_id": str(action.installment_id)},
    )
    db.commit()
    db.refresh(action)
    creator_name = db.scalar(select(User.full_name).where(User.id == action.created_by_user_id)) or "Equipe"
    return collection_action_read(action, creator_name, actor.full_name)


def owned_client(db: Session, client_id: uuid.UUID, org_id: uuid.UUID) -> Client:
    client = db.scalar(
        select(Client).where(
            Client.id == client_id,
            Client.organization_id == org_id,
        )
    )
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


@router.post("/clients/{client_id}/incomes", response_model=IncomeRead, status_code=201)
def add_income(
    client_id: uuid.UUID,
    payload: IncomeCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    income = Income(client_id=client_id, **payload.model_dump())
    db.add(income)
    db.flush()
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="income",
        entity_id=income.id,
        action="create",
        new_values={"amount": str(income.net_amount)},
    )
    db.commit()
    db.refresh(income)
    return income


@router.get("/clients/{client_id}/incomes", response_model=list[IncomeRead])
def list_incomes(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    owned_client(db, client_id, actor.organization_id)
    return list(db.scalars(select(Income).where(Income.client_id == client_id)))


@router.put("/clients/{client_id}/incomes/{income_id}", response_model=IncomeRead)
def update_income(
    client_id: uuid.UUID,
    income_id: uuid.UUID,
    payload: IncomeCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    income = db.scalar(
        select(Income).where(
            Income.id == income_id,
            Income.client_id == client_id,
        )
    )
    if not income:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    for field, value in payload.model_dump().items():
        setattr(income, field, value)
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="income",
        entity_id=income.id,
        action="update",
        new_values={"amount": str(income.net_amount)},
    )
    db.commit()
    db.refresh(income)
    return income


@router.delete(
    "/clients/{client_id}/incomes/{income_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_income(
    client_id: uuid.UUID,
    income_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    income = db.scalar(
        select(Income).where(
            Income.id == income_id,
            Income.client_id == client_id,
        )
    )
    if not income:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="income",
        entity_id=income.id,
        action="delete",
        new_values={"amount": str(income.net_amount)},
    )
    db.delete(income)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/clients/{client_id}/expenses", response_model=ExpenseRead, status_code=201)
def add_expense(
    client_id: uuid.UUID,
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    expense = Expense(client_id=client_id, **payload.model_dump())
    db.add(expense)
    db.flush()
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="expense",
        entity_id=expense.id,
        action="create",
        new_values={"amount": str(expense.amount)},
    )
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/clients/{client_id}/expenses", response_model=list[ExpenseRead])
def list_expenses(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    owned_client(db, client_id, actor.organization_id)
    return list(db.scalars(select(Expense).where(Expense.client_id == client_id)))


@router.put("/clients/{client_id}/expenses/{expense_id}", response_model=ExpenseRead)
def update_expense(
    client_id: uuid.UUID,
    expense_id: uuid.UUID,
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    expense = db.scalar(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.client_id == client_id,
        )
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    for field, value in payload.model_dump().items():
        setattr(expense, field, value)
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="expense",
        entity_id=expense.id,
        action="update",
        new_values={"amount": str(expense.amount)},
    )
    db.commit()
    db.refresh(expense)
    return expense


@router.delete(
    "/clients/{client_id}/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_expense(
    client_id: uuid.UUID,
    expense_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    expense = db.scalar(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.client_id == client_id,
        )
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="expense",
        entity_id=expense.id,
        action="delete",
        new_values={"amount": str(expense.amount)},
    )
    db.delete(expense)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/creditors", response_model=CreditorRead, status_code=201)
def add_creditor(
    payload: CreditorCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    creditor = Creditor(
        organization_id=actor.organization_id,
        **payload.model_dump(),
    )
    db.add(creditor)
    db.flush()
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="creditor",
        entity_id=creditor.id,
        action="create",
        new_values={"legal_name": creditor.legal_name},
    )
    db.commit()
    db.refresh(creditor)
    return creditor


@router.get("/creditors", response_model=list[CreditorRead])
def list_creditors(
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    return list(
        db.scalars(
            select(Creditor)
            .where(Creditor.organization_id == actor.organization_id)
            .order_by(Creditor.legal_name)
        )
    )


@router.post("/clients/{client_id}/debts", response_model=DebtRead, status_code=201)
def add_debt(
    client_id: uuid.UUID,
    payload: DebtCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    if payload.creditor_id and not db.scalar(
        select(Creditor).where(
            Creditor.id == payload.creditor_id,
            Creditor.organization_id == actor.organization_id,
        )
    ):
        raise HTTPException(status_code=404, detail="Credor não encontrado")
    debt = Debt(
        organization_id=actor.organization_id,
        client_id=client_id,
        **payload.model_dump(),
    )
    db.add(debt)
    db.flush()
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="debt",
        entity_id=debt.id,
        action="create",
        new_values={
            "nature": debt.nature,
            "current_balance": str(debt.current_balance),
            "monthly_installment": str(debt.monthly_installment),
        },
    )
    db.commit()
    db.refresh(debt)
    return debt


@router.get("/clients/{client_id}/debts", response_model=list[DebtRead])
def list_debts(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    owned_client(db, client_id, actor.organization_id)
    return list(
        db.scalars(
            select(Debt).where(
                Debt.client_id == client_id,
                Debt.organization_id == actor.organization_id,
            )
        )
    )


@router.put("/clients/{client_id}/debts/{debt_id}", response_model=DebtRead)
def update_debt(
    client_id: uuid.UUID,
    debt_id: uuid.UUID,
    payload: DebtCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    debt = db.scalar(
        select(Debt).where(
            Debt.id == debt_id,
            Debt.client_id == client_id,
            Debt.organization_id == actor.organization_id,
        )
    )
    if not debt:
        raise HTTPException(status_code=404, detail="Dívida não encontrada")
    if payload.creditor_id and not db.scalar(
        select(Creditor).where(
            Creditor.id == payload.creditor_id,
            Creditor.organization_id == actor.organization_id,
        )
    ):
        raise HTTPException(status_code=404, detail="Credor não encontrado")
    for field, value in payload.model_dump().items():
        setattr(debt, field, value)
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="debt",
        entity_id=debt.id,
        action="update",
        new_values={
            "nature": debt.nature,
            "current_balance": str(debt.current_balance),
            "monthly_installment": str(debt.monthly_installment),
        },
    )
    db.commit()
    db.refresh(debt)
    return debt


@router.delete(
    "/clients/{client_id}/debts/{debt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_debt(
    client_id: uuid.UUID,
    debt_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    debt = db.scalar(
        select(Debt).where(
            Debt.id == debt_id,
            Debt.client_id == client_id,
            Debt.organization_id == actor.organization_id,
        )
    )
    if not debt:
        raise HTTPException(status_code=404, detail="Dívida não encontrada")
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="debt",
        entity_id=debt.id,
        action="delete",
        new_values={
            "nature": debt.nature,
            "current_balance": str(debt.current_balance),
        },
    )
    db.delete(debt)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def owned_agreement(
    db: Session,
    client_id: uuid.UUID,
    agreement_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> PaymentAgreement:
    agreement = db.scalar(
        select(PaymentAgreement).options(selectinload(PaymentAgreement.installments)).where(
            PaymentAgreement.id == agreement_id,
            PaymentAgreement.client_id == client_id,
            PaymentAgreement.organization_id == organization_id,
        )
    )
    if not agreement:
        raise HTTPException(status_code=404, detail="Acordo não encontrado")
    return agreement


def validate_agreement_debt(
    db: Session,
    client_id: uuid.UUID,
    debt_id: uuid.UUID | None,
    organization_id: uuid.UUID,
) -> None:
    if debt_id is None:
        return
    exists = db.scalar(
        select(Debt.id).where(
            Debt.id == debt_id,
            Debt.client_id == client_id,
            Debt.organization_id == organization_id,
        )
    )
    if not exists:
        raise HTTPException(status_code=422, detail="A dívida selecionada não pertence a este cliente")


@router.post(
    "/clients/{client_id}/agreements",
    response_model=PaymentAgreementRead,
    status_code=status.HTTP_201_CREATED,
)
def add_payment_agreement(
    client_id: uuid.UUID,
    payload: PaymentAgreementCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    validate_agreement_debt(db, client_id, payload.debt_id, actor.organization_id)
    agreement = PaymentAgreement(
        organization_id=actor.organization_id,
        client_id=client_id,
        **payload.model_dump(),
    )
    db.add(agreement)
    db.flush()
    agreement.installments.extend(build_installments(agreement))
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="payment_agreement",
        entity_id=agreement.id,
        action="create",
        new_values={
            "title": agreement.title,
            "status": agreement.status,
            "payment_method": agreement.payment_method,
            "negotiated_amount": str(agreement.negotiated_amount),
        },
    )
    db.commit()
    return owned_agreement(db, client_id, agreement.id, actor.organization_id)


@router.get(
    "/clients/{client_id}/agreements",
    response_model=list[PaymentAgreementRead],
)
def list_payment_agreements(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    owned_client(db, client_id, actor.organization_id)
    agreements = list(
        db.scalars(
            select(PaymentAgreement).options(selectinload(PaymentAgreement.installments))
            .where(
                PaymentAgreement.client_id == client_id,
                PaymentAgreement.organization_id == actor.organization_id,
            )
            .order_by(PaymentAgreement.created_at.desc(), PaymentAgreement.id)
        )
    )
    statuses_changed = False
    for agreement in agreements:
        statuses_changed = sync_installment_statuses(agreement) or statuses_changed
    if statuses_changed:
        db.commit()
    return agreements


@router.put(
    "/clients/{client_id}/agreements/{agreement_id}",
    response_model=PaymentAgreementRead,
)
def update_payment_agreement(
    client_id: uuid.UUID,
    agreement_id: uuid.UUID,
    payload: PaymentAgreementCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    validate_agreement_debt(db, client_id, payload.debt_id, actor.organization_id)
    agreement = owned_agreement(db, client_id, agreement_id, actor.organization_id)
    schedule_fields = {"negotiated_amount", "down_payment", "installment_count", "installment_amount", "first_due_date"}
    schedule_changed = any(getattr(agreement, field) != getattr(payload, field) for field in schedule_fields)
    if schedule_changed and any(item.status == "paid" for item in agreement.installments):
        raise HTTPException(
            status_code=409,
            detail="O plano não pode ser alterado porque já existem parcelas pagas. Estorne os pagamentos antes de modificar valores ou vencimentos.",
        )
    for field, value in payload.model_dump().items():
        setattr(agreement, field, value)
    if schedule_changed:
        agreement.installments.clear()
        db.flush()
        agreement.installments.extend(build_installments(agreement))
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="payment_agreement",
        entity_id=agreement.id,
        action="update",
        new_values={
            "title": agreement.title,
            "status": agreement.status,
            "payment_method": agreement.payment_method,
            "negotiated_amount": str(agreement.negotiated_amount),
        },
    )
    db.commit()
    return owned_agreement(db, client_id, agreement.id, actor.organization_id)


@router.post(
    "/clients/{client_id}/agreements/{agreement_id}/installments/generate",
    response_model=list[PaymentInstallmentRead],
)
def generate_payment_installments(
    client_id: uuid.UUID,
    agreement_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    agreement = owned_agreement(db, client_id, agreement_id, actor.organization_id)
    if agreement.installments:
        raise HTTPException(status_code=409, detail="Este acordo já possui parcelas geradas")
    agreement.installments.extend(build_installments(agreement))
    if not agreement.installments:
        raise HTTPException(status_code=422, detail="O acordo não possui saldo parcelável")
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="payment_installment",
        entity_id=agreement.id,
        action="create",
        new_values={"title": agreement.title, "count": len(agreement.installments)},
    )
    db.commit()
    return agreement.installments


def owned_installment(
    agreement: PaymentAgreement,
    installment_id: uuid.UUID,
) -> PaymentInstallment:
    installment = next((item for item in agreement.installments if item.id == installment_id), None)
    if not installment:
        raise HTTPException(status_code=404, detail="Parcela não encontrada")
    return installment


@router.put(
    "/clients/{client_id}/agreements/{agreement_id}/installments/{installment_id}/payment",
    response_model=PaymentInstallmentRead,
)
def register_installment_payment(
    client_id: uuid.UUID,
    agreement_id: uuid.UUID,
    installment_id: uuid.UUID,
    payload: InstallmentPaymentCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    agreement = owned_agreement(db, client_id, agreement_id, actor.organization_id)
    installment = owned_installment(agreement, installment_id)
    if payload.paid_amount != installment.amount:
        raise HTTPException(
            status_code=422,
            detail="O valor pago deve ser igual ao valor da parcela",
        )
    installment.paid_amount = payload.paid_amount
    installment.paid_at = payload.paid_at
    installment.payment_method = payload.payment_method
    installment.payment_notes = payload.payment_notes
    installment.status = "paid"
    db.flush()
    if agreement.installments and all(item.status == "paid" for item in agreement.installments):
        agreement.status = "completed"
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="payment_installment",
        entity_id=installment.id,
        action="update",
        new_values={
            "title": agreement.title,
            "installment_number": installment.installment_number,
            "amount": str(installment.paid_amount),
            "payment_method": installment.payment_method,
            "status": installment.status,
        },
    )
    db.commit()
    db.refresh(installment)
    return installment


@router.delete(
    "/clients/{client_id}/agreements/{agreement_id}/installments/{installment_id}/payment",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reverse_installment_payment(
    client_id: uuid.UUID,
    agreement_id: uuid.UUID,
    installment_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    agreement = owned_agreement(db, client_id, agreement_id, actor.organization_id)
    installment = owned_installment(agreement, installment_id)
    if installment.status != "paid":
        raise HTTPException(status_code=409, detail="Esta parcela não possui pagamento para estornar")
    previous_amount = installment.paid_amount
    installment.paid_amount = Decimal("0")
    installment.paid_at = None
    installment.payment_method = None
    installment.payment_notes = None
    installment.status = "overdue" if installment.due_date < date.today() else "pending"
    if agreement.status == "completed":
        agreement.status = "active"
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="payment_installment",
        entity_id=installment.id,
        action="delete",
        new_values={
            "title": agreement.title,
            "installment_number": installment.installment_number,
            "amount": str(previous_amount),
            "status": installment.status,
        },
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/clients/{client_id}/agreements/{agreement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_payment_agreement(
    client_id: uuid.UUID,
    agreement_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("admin", "lawyer", "team")),
):
    owned_client(db, client_id, actor.organization_id)
    agreement = owned_agreement(db, client_id, agreement_id, actor.organization_id)
    if any(item.status == "paid" for item in agreement.installments):
        raise HTTPException(
            status_code=409,
            detail="Este acordo possui pagamentos registrados. Estorne os pagamentos antes de apagar o acordo.",
        )
    record_audit(
        db,
        organization_id=actor.organization_id,
        user_id=actor.id,
        entity_type="payment_agreement",
        entity_id=agreement.id,
        action="delete",
        new_values={
            "title": agreement.title,
            "status": agreement.status,
            "negotiated_amount": str(agreement.negotiated_amount),
        },
    )
    db.delete(agreement)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
