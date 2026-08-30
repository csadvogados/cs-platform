from __future__ import annotations

import csv
import io
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.recovery import JudicialProcess
from app.schemas.judicial_report import JudicialMetric, JudicialMonthlyMetric, JudicialReportRead
from app.security.identity import IdentityContext
from app.security.permissions import PermissionCode
from app.services.audit import record_audit

router = APIRouter()

OUTCOME_LABELS = {
    "favorable": "Favorável", "partially_favorable": "Parcialmente favorável",
    "unfavorable": "Desfavorável", "settlement": "Acordo judicial",
    "dismissed": "Extinto sem decisão de mérito", "other": "Outro resultado",
}
STATUS_LABELS = {
    "filed": "Protocolado", "awaiting_decision": "Aguardando decisão",
    "hearing_scheduled": "Audiência marcada", "decision_issued": "Decisão proferida",
    "appeal": "Em recurso", "closed": "Encerrado",
}


def build_judicial_report(db: Session, organization_id, date_from: date | None, date_to: date | None) -> JudicialReportRead:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="A data inicial não pode ser posterior à data final")
    if date_from and date_to and (date_to - date_from).days > 3660:
        raise HTTPException(status_code=422, detail="O período máximo do relatório é de 10 anos")
    rows = list(db.scalars(select(JudicialProcess).where(JudicialProcess.organization_id == organization_id)))
    if date_from:
        rows = [row for row in rows if row.created_at.date() >= date_from]
    if date_to:
        rows = [row for row in rows if row.created_at.date() <= date_to]
    now = datetime.now(timezone.utc)
    today = now.date()
    active = [row for row in rows if row.status != "closed"]
    closed = [row for row in rows if row.status == "closed"]
    durations = []
    for row in closed:
        start = row.filed_at or row.created_at
        end = row.closed_at or row.updated_at
        if start and end:
            # SQLite returns naive datetimes while PostgreSQL keeps timezone data.
            # Normalizing here keeps the report portable across tests and production.
            durations.append(max(0, (end.replace(tzinfo=None) - start.replace(tzinfo=None)).total_seconds() / 86400))
    outcomes = Counter(row.outcome for row in closed if row.outcome)
    statuses = Counter(row.status for row in rows)
    monthly = Counter((row.closed_at or row.updated_at).strftime("%Y-%m") for row in closed)
    favorable = outcomes["favorable"] + outcomes["partially_favorable"] + outcomes["settlement"]
    return JudicialReportRead(
        date_from=date_from, date_to=date_to, total=len(rows), active=len(active), closed=len(closed),
        overdue_deadlines=sum(bool(row.next_deadline and row.next_deadline.date() < today) for row in active),
        deadlines_next_7_days=sum(bool(row.next_deadline and today <= row.next_deadline.date() <= today + timedelta(days=7)) for row in active),
        average_duration_days=round(sum(durations) / len(durations), 1) if durations else 0,
        favorable_rate=round(favorable / len(closed) * 100, 1) if closed else 0,
        outcomes=[JudicialMetric(key=key, label=OUTCOME_LABELS.get(key, key), count=count) for key, count in sorted(outcomes.items())],
        statuses=[JudicialMetric(key=key, label=STATUS_LABELS.get(key, key), count=count) for key, count in sorted(statuses.items())],
        monthly_closures=[JudicialMonthlyMetric(month=month, closed=count) for month, count in sorted(monthly.items())[-12:]],
    )


@router.get("/summary", response_model=JudicialReportRead)
def judicial_report(date_from: date | None = None, date_to: date | None = None,
                    db: Session = Depends(get_db),
                    identity: IdentityContext = Depends(require_permissions(PermissionCode.JUDICIAL_REPORT_READ.value))):
    return build_judicial_report(db, identity.organization_id, date_from, date_to)


@router.get("/summary.csv")
def export_judicial_report(date_from: date | None = None, date_to: date | None = None,
                           db: Session = Depends(get_db),
                           identity: IdentityContext = Depends(require_permissions(
                               PermissionCode.JUDICIAL_REPORT_READ.value, PermissionCode.JUDICIAL_REPORT_EXPORT.value))):
    report = build_judicial_report(db, identity.organization_id, date_from, date_to)
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";")
    writer.writerow(["Relatório judicial", "CS Platform"])
    writer.writerow(["Período", report.date_from or "Completo", report.date_to or "Completo"])
    writer.writerow([])
    writer.writerow(["Indicador", "Valor"])
    writer.writerow(["Processos", report.total]); writer.writerow(["Ativos", report.active]); writer.writerow(["Encerrados", report.closed])
    writer.writerow(["Prazos vencidos", report.overdue_deadlines]); writer.writerow(["Prazos nos próximos 7 dias", report.deadlines_next_7_days])
    writer.writerow(["Duração média em dias", report.average_duration_days]); writer.writerow(["Resultados favoráveis (%)", report.favorable_rate])
    writer.writerow([]); writer.writerow(["Resultados", "Quantidade"])
    for item in report.outcomes: writer.writerow([item.label, item.count])
    record_audit(db, organization_id=identity.organization_id, user_id=identity.user_id,
                 entity_type="judicial_report", entity_id=None, action="export",
                 new_values={"date_from": str(date_from), "date_to": str(date_to)})
    db.commit()
    return Response(content=("\ufeff" + stream.getvalue()).encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="relatorio_judicial.csv"', "Cache-Control": "no-store"})
