from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from html import escape

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.document import ClientDocument
from app.models.financial import Diagnosis, PaymentAgreement
from app.models.negotiation import Negotiation
from app.models.recovery import JudicialProcess, RecoveryCase
from app.services.diagnosis_engine import calculate


REQUIRED_DOCUMENTS = ["identification", "income_proof", "residence_proof", "debt_statement"]


def build_judicial_dossier(db: Session, client) -> dict:
    organization_id = client.organization_id
    diagnosis = db.scalar(select(Diagnosis).where(
        Diagnosis.organization_id == organization_id, Diagnosis.client_id == client.id
    ).order_by(Diagnosis.version.desc(), Diagnosis.created_at.desc()).limit(1))
    cases = list(db.scalars(select(RecoveryCase).options(
        selectinload(RecoveryCase.judicial_process).selectinload(JudicialProcess.events)
    ).where(RecoveryCase.organization_id == organization_id, RecoveryCase.client_id == client.id,
            RecoveryCase.deleted_at.is_(None)).order_by(RecoveryCase.created_at)))
    negotiations = list(db.scalars(select(Negotiation).options(selectinload(Negotiation.offers)).where(
        Negotiation.organization_id == organization_id, Negotiation.client_id == client.id
    ).order_by(Negotiation.opened_at)))
    agreements = list(db.scalars(select(PaymentAgreement).where(
        PaymentAgreement.organization_id == organization_id, PaymentAgreement.client_id == client.id
    ).order_by(PaymentAgreement.created_at)))
    documents = list(db.scalars(select(ClientDocument).where(
        ClientDocument.organization_id == organization_id, ClientDocument.client_id == client.id,
        ClientDocument.deleted_at.is_(None)).order_by(ClientDocument.created_at)))
    summary = calculate(client, Decimal(str(settings.minimum_existential_reference)))
    validated = sorted({item.category for item in documents if item.status == "validated"})
    missing_documents = [item for item in REQUIRED_DOCUMENTS if item not in validated]
    missing_information = []
    if not client.incomes: missing_information.append("Renda não cadastrada.")
    if not client.expenses: missing_information.append("Despesas essenciais não cadastradas.")
    if not client.debts: missing_information.append("Dívidas não cadastradas.")
    if diagnosis is None: missing_information.append("Diagnóstico ainda não salvo.")
    if client.good_faith_declared is None: missing_information.append("Declaração de boa-fé não confirmada.")
    if client.can_pay_without_harming_basics is None: missing_information.append("Capacidade de pagamento não confirmada.")
    debts = [{"id": str(x.id), "creditor": x.creditor.legal_name if x.creditor else "Não informado",
              "nature": x.nature, "balance": x.current_balance, "installment": x.monthly_installment,
              "overdue": x.overdue} for x in client.debts]
    negotiation_rows = []
    timeline = []
    for case in cases:
        timeline.append({"date": case.created_at, "type": "case_opened", "title": f"Caso {case.case_number} criado"})
        if case.judicial_process:
            for event in case.judicial_process.events:
                timeline.append({"date": event.event_date, "type": event.event_type, "title": event.title,
                                 "description": event.description})
    for item in negotiations:
        timeline.append({"date": item.opened_at, "type": "negotiation_opened", "title": "Negociação aberta"})
        negotiation_rows.append({"id": str(item.id), "case_id": str(item.recovery_case_id), "debt_id": str(item.debt_id),
            "status": item.status, "channel": item.channel, "opened_at": item.opened_at,
            "offers": [{"sequence": offer.sequence_number, "origin": offer.origin, "amount": offer.offered_amount,
                        "installments": offer.installment_count, "installment_amount": offer.installment_amount,
                        "score": offer.engine_score, "decision": offer.engine_decision, "status": offer.status,
                        "created_at": offer.created_at} for offer in item.offers]})
        for offer in item.offers:
            timeline.append({"date": offer.created_at, "type": "offer", "title": f"Proposta {offer.sequence_number}",
                             "description": f"{offer.installment_count} parcela(s) de R$ {_money(offer.installment_amount)} — {offer.status}"})
    return {
        "generated_at": datetime.now(timezone.utc),
        "client": {"id": str(client.id), "name": client.full_name, "cpf": client.cpf, "profession": client.profession,
                   "email": client.email, "phone": client.phone, "city": client.city, "state": client.state,
                   "good_faith": client.good_faith_declared, "payment_capacity_confirmed": client.can_pay_without_harming_basics},
        "financial": summary,
        "diagnosis": ({"version": diagnosis.version, "result": diagnosis.eligibility_result,
                       "score": diagnosis.eligibility_score, "data_quality_score": diagnosis.data_quality_score,
                       "risk_level": diagnosis.risk_level, "strategy": diagnosis.recommended_strategy,
                       "conclusion": diagnosis.economic_conclusion, "legal_alerts": diagnosis.legal_alerts.splitlines()}
                      if diagnosis else None),
        "debts": debts,
        "negotiations": negotiation_rows,
        "agreements": [{"title": x.title, "status": x.status, "original_amount": x.original_amount,
                        "negotiated_amount": x.negotiated_amount, "down_payment": x.down_payment,
                        "installments": x.installment_count, "installment_amount": x.installment_amount,
                        "first_due_date": x.first_due_date} for x in agreements],
        "documents": [{"category": x.category, "filename": x.filename, "status": x.status,
                       "validated_at": x.validated_at} for x in documents],
        "checklist": {"required": REQUIRED_DOCUMENTS, "validated": validated, "missing": missing_documents,
                      "ready": not missing_documents and not missing_information},
        "cases": [{"number": x.case_number, "status": x.status, "stage": x.stage, "opened_at": x.opened_at,
                   "judicial_process": ({"number": x.judicial_process.process_number, "court": x.judicial_process.court,
                                         "status": x.judicial_process.status, "next_deadline": x.judicial_process.next_deadline}
                                        if x.judicial_process else None)} for x in cases],
        "timeline": sorted(timeline, key=lambda item: item["date"].replace(tzinfo=None) if item["date"] else datetime.min),
        "missing_information": missing_information,
    }


def _money(value) -> str:
    return f"{Decimal(value or 0):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def render_judicial_dossier(data: dict) -> str:
    client, financial = data["client"], data["financial"]
    rows = "".join(f"<tr><td>{escape(x['creditor'])}</td><td>{escape(x['nature'])}</td><td>R$ {_money(x['balance'])}</td><td>R$ {_money(x['installment'])}</td><td>{'Em atraso' if x['overdue'] else 'Em dia'}</td></tr>" for x in data["debts"]) or '<tr><td colspan="5">Nenhuma dívida cadastrada.</td></tr>'
    negotiations = "".join(f"<li><strong>{escape(x['channel'])}</strong> — {escape(x['status'])}; {len(x['offers'])} proposta(s).</li>" for x in data["negotiations"]) or "<li>Nenhuma negociação registrada.</li>"
    agreements = "".join(f"<li><strong>{escape(x['title'])}</strong> — R$ {_money(x['negotiated_amount'])}, {x['installments']} × R$ {_money(x['installment_amount'])} ({escape(x['status'])}).</li>" for x in data["agreements"]) or "<li>Nenhum acordo registrado.</li>"
    documents = "".join(f"<li>{escape(x['filename'])} — {escape(x['category'])} ({escape(x['status'])})</li>" for x in data["documents"]) or "<li>Nenhum documento enviado.</li>"
    timeline = "".join(f"<li><strong>{x['date'].strftime('%d/%m/%Y') if x.get('date') else 'Sem data'}</strong> — {escape(x['title'])}{': ' + escape(x['description']) if x.get('description') else ''}</li>" for x in data["timeline"]) or "<li>Nenhum evento registrado.</li>"
    pending = data["missing_information"] + [f"Documento pendente: {x}" for x in data["checklist"]["missing"]]
    pending_html = "".join(f"<li>{escape(x)}</li>" for x in pending) or "<li>Sem pendências automáticas.</li>"
    diagnosis = data.get("diagnosis") or {}
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Dossiê judicial — {escape(client['name'])}</title><style>
    body{{margin:0;background:#e9e5dc;color:#17231e;font:14px Arial;line-height:1.5}}.toolbar{{position:sticky;top:0;padding:12px;text-align:center;background:#0d3025}}button{{padding:10px 18px;border-radius:8px;border:1px solid #fff;background:#fff;color:#0d3025;font-weight:700}}.page{{max-width:920px;margin:24px auto;background:#fff}}header{{padding:32px 38px;background:#0d3025;color:#fff}}main{{padding:30px 38px}}h1,h2{{font-family:Georgia,serif;font-weight:500}}h1{{margin:6px 0}}h2{{margin-top:28px;border-bottom:1px solid #d9d4ca;padding-bottom:8px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#d9d4ca;border:1px solid #d9d4ca}}.grid div{{background:#fff;padding:15px}}.grid span{{display:block;font-size:10px;text-transform:uppercase;color:#68736d}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border:1px solid #d9d4ca;text-align:left}}th{{background:#f4f0e7}}.notice{{padding:15px;background:#fbf7ec;border-left:4px solid #d4a74f}}footer{{padding:18px;text-align:center;border-top:1px solid #ddd;font-size:11px}}@media print{{.toolbar{{display:none}}body{{background:#fff}}.page{{margin:0;max-width:none}}}}@media(max-width:700px){{.grid{{grid-template-columns:1fr}}}}
    </style></head><body><div class="toolbar"><button onclick="window.print()">Imprimir / Salvar como PDF</button></div><article class="page"><header><strong>CS Platform</strong><p>DOSSIÊ DE JUDICIALIZAÇÃO</p><h1>{escape(client['name'])}</h1><span>Gerado em {data['generated_at'].strftime('%d/%m/%Y %H:%M UTC')}</span></header><main>
    <h2>1. Identificação</h2><p><strong>CPF:</strong> {escape(client['cpf'] or 'Não informado')} · <strong>Profissão:</strong> {escape(client['profession'] or 'Não informada')} · <strong>Contato:</strong> {escape(client['email'] or client['phone'] or 'Não informado')}</p>
    <h2>2. Síntese econômica</h2><div class="grid"><div><span>Renda</span><strong>R$ {_money(financial['total_income'])}</strong></div><div><span>Despesas essenciais</span><strong>R$ {_money(financial['total_expenses'])}</strong></div><div><span>Capacidade máxima</span><strong>R$ {_money(financial['max_payment_capacity'])}</strong></div><div><span>Dívidas</span><strong>R$ {_money(financial['total_debt_balance'])}</strong></div><div><span>Comprometimento</span><strong>{financial['commitment_percentage']}%</strong></div><div><span>Qualidade dos dados</span><strong>{financial['data_quality_score']}%</strong></div></div>
    <h2>3. Diagnóstico</h2><p><strong>{escape(str(diagnosis.get('result','Não salvo')))}</strong> — {escape(str(diagnosis.get('conclusion', financial.get('economic_conclusion','Sem conclusão.'))))}</p>
    <h2>4. Quadro de credores e dívidas</h2><table><thead><tr><th>Credor</th><th>Natureza</th><th>Saldo</th><th>Parcela</th><th>Situação</th></tr></thead><tbody>{rows}</tbody></table>
    <h2>5. Negociações e propostas</h2><ul>{negotiations}</ul><h2>6. Acordos</h2><ul>{agreements}</ul><h2>7. Cronologia</h2><ul>{timeline}</ul><h2>8. Documentos</h2><ul>{documents}</ul><h2>9. Pendências para revisão</h2><ul>{pending_html}</ul>
    <h2>10. Conclusão e revisão profissional</h2><div class="notice">Documento consolidado automaticamente a partir dos registros da CS Platform. Deve ser revisado pelo advogado responsável antes de qualquer protocolo ou utilização judicial.</div></main><footer>CS Platform — Gestão jurídica inteligente</footer></article></body></html>'''
