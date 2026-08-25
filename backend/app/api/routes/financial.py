import calendar
import uuid
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.client import Client
from app.models.financial import Creditor, Debt, Expense, Income, PaymentAgreement, PaymentInstallment
from app.models.user import User
from app.schemas.financial import (
    CreditorCreate,
    CreditorRead,
    CollectionItemRead,
    CollectionSummaryRead,
    CollectionsRead,
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


@router.get("/collections", response_model=CollectionsRead)
def list_collections(
    q: str = Query(default="", max_length=200),
    collection_status_filter: str = Query(default="all", alias="status"),
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

    rows = db.execute(
        select(PaymentInstallment, PaymentAgreement, Client)
        .join(PaymentAgreement, PaymentAgreement.id == PaymentInstallment.agreement_id)
        .join(Client, Client.id == PaymentInstallment.client_id)
        .where(PaymentInstallment.organization_id == actor.organization_id)
        .order_by(PaymentInstallment.due_date, Client.full_name, PaymentInstallment.installment_number)
    ).all()
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
    summary = CollectionSummaryRead(
        open_count=len(open_items),
        open_amount=sum((item.amount for item in open_items), Decimal("0")),
        overdue_count=len(overdue_items),
        overdue_amount=sum((item.amount for item in overdue_items), Decimal("0")),
        due_soon_count=len(due_soon_items),
        due_soon_amount=sum((item.amount for item in due_soon_items), Decimal("0")),
        paid_this_month_count=len(paid_this_month),
        paid_this_month_amount=sum((item.paid_amount for item in paid_this_month), Decimal("0")),
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

    return CollectionsRead(summary=summary, items=items, total=len(items))


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
