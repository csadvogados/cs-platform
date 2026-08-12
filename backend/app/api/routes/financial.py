import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.client import Client
from app.models.financial import Creditor, Debt, Expense, Income, PaymentAgreement
from app.models.user import User
from app.schemas.financial import (
    CreditorCreate,
    CreditorRead,
    DebtCreate,
    DebtRead,
    ExpenseCreate,
    ExpenseRead,
    IncomeCreate,
    IncomeRead,
    PaymentAgreementCreate,
    PaymentAgreementRead,
)
from app.services.audit import record_audit

router = APIRouter()


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
        select(PaymentAgreement).where(
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
    db.refresh(agreement)
    return agreement


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
    return list(
        db.scalars(
            select(PaymentAgreement)
            .where(
                PaymentAgreement.client_id == client_id,
                PaymentAgreement.organization_id == actor.organization_id,
            )
            .order_by(PaymentAgreement.created_at.desc(), PaymentAgreement.id)
        )
    )


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
    for field, value in payload.model_dump().items():
        setattr(agreement, field, value)
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
    db.refresh(agreement)
    return agreement


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
