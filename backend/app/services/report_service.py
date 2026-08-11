from datetime import datetime, timezone
from decimal import Decimal
from html import escape


def brl(value) -> str:
    formatted = f"{Decimal(value or 0):,.2f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def cpf_display(value: str | None) -> str:
    digits = "".join(character for character in str(value or "") if character.isdigit())
    if len(digits) != 11:
        return escape(str(value or "Não informado"))
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _render_report(client, data: dict, *, version: int | None = None, saved_at=None) -> str:
    alerts = data.get("legal_alerts") or []
    if isinstance(alerts, str):
        alerts = [line.strip() for line in alerts.splitlines() if line.strip()]
    alerts_html = "".join(f"<li>{escape(str(alert))}</li>" for alert in alerts)
    if not alerts_html:
        alerts_html = "<li>Sem alertas adicionais.</li>"

    commitment = Decimal(data.get("commitment_percentage") or 0)
    width = max(0, min(float(commitment), 100))
    generated_at = datetime.now(timezone.utc)
    reference_at = saved_at or generated_at
    reference_text = reference_at.strftime("%d/%m/%Y às %H:%M UTC")
    report_label = f"Versão {version} salva" if version is not None else "Prévia atual"

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Diagnóstico financeiro — {escape(client.full_name)}</title>
  <style>
    :root {{ --forest:#0d3025; --forest-2:#1f5746; --cream:#f4f0e7; --gold:#d4a74f; --ink:#15211c; --line:#d9d4ca; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:#e9e5dc; font-family:Arial,Helvetica,sans-serif; line-height:1.5; }}
    .toolbar {{ position:sticky; top:0; z-index:2; display:flex; justify-content:center; gap:10px; padding:12px; background:rgba(13,48,37,.96); }}
    .toolbar button {{ border:1px solid rgba(255,255,255,.5); border-radius:8px; padding:10px 18px; color:#fff; background:transparent; cursor:pointer; font-weight:700; }}
    .toolbar button.primary {{ color:var(--forest); background:#fff; }}
    .page {{ width:min(920px,calc(100% - 32px)); margin:26px auto; background:#fff; box-shadow:0 18px 60px rgba(13,48,37,.14); }}
    header {{ padding:32px 38px; color:#fff; background:var(--forest); }}
    .brand {{ display:flex; align-items:center; gap:12px; font-weight:800; }}
    .brand-mark {{ display:grid; place-items:center; width:38px; height:38px; border-radius:8px; color:var(--forest); background:var(--cream); font-family:Georgia,serif; }}
    .kicker {{ margin:34px 0 7px; color:#91c8b4; font-size:11px; font-weight:800; letter-spacing:.14em; text-transform:uppercase; }}
    h1 {{ margin:0; font-family:Georgia,serif; font-size:37px; font-weight:500; }}
    .report-meta {{ display:flex; flex-wrap:wrap; gap:8px 22px; margin-top:17px; color:#d7e6df; font-size:12px; }}
    main {{ padding:32px 38px 40px; }}
    .client {{ display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-bottom:24px; padding:18px; border:1px solid var(--line); background:var(--cream); }}
    .client span,.metric span {{ display:block; margin-bottom:5px; color:#68736d; font-size:10px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }}
    .metrics {{ display:grid; grid-template-columns:repeat(5,1fr); border:1px solid var(--line); }}
    .metric {{ min-height:105px; padding:17px; border-right:1px solid var(--line); }}
    .metric:last-child {{ border-right:0; }}
    .metric strong {{ font-family:Georgia,serif; font-size:25px; font-weight:500; }}
    .section {{ margin-top:28px; }}
    h2 {{ margin:0 0 14px; font-family:Georgia,serif; font-size:24px; font-weight:500; }}
    .bar {{ height:14px; overflow:hidden; border-radius:999px; background:#dce4df; }}
    .bar span {{ display:block; height:100%; background:var(--gold); }}
    .commitment {{ display:flex; justify-content:space-between; gap:15px; margin-top:8px; color:#66716b; font-size:12px; }}
    .score {{ display:grid; grid-template-columns:130px 1fr; gap:22px; align-items:center; padding:22px; color:#fff; background:var(--forest-2); }}
    .score-number {{ font-family:Georgia,serif; font-size:49px; text-align:center; }}
    .score-number small {{ display:block; font-family:Arial,sans-serif; font-size:10px; letter-spacing:.08em; text-transform:uppercase; }}
    .score p {{ margin:6px 0 0; color:#d5e7df; }}
    .conclusion {{ padding:20px; background:var(--cream); }}
    .conclusion p {{ margin:0; }}
    ul {{ margin:10px 0 0; padding-left:20px; color:#56625c; }}
    .notice {{ margin-top:28px; padding:15px 17px; border-left:4px solid var(--gold); background:#fbf7ec; font-size:12px; }}
    .signatures {{ display:grid; grid-template-columns:1fr 1fr; gap:50px; margin-top:55px; }}
    .signature {{ padding-top:8px; border-top:1px solid #797f7b; color:#68736d; font-size:11px; text-align:center; }}
    footer {{ padding:18px 38px; border-top:1px solid var(--line); color:#7b847f; font-size:10px; text-align:center; }}
    @media (max-width:700px) {{ .metrics {{ grid-template-columns:1fr; }} .metric {{ border-right:0; border-bottom:1px solid var(--line); }} .metric:last-child {{ border-bottom:0; }} .client,.score,.signatures {{ grid-template-columns:1fr; }} }}
    @media print {{ @page {{ size:A4; margin:12mm; }} body {{ background:#fff; }} .toolbar {{ display:none; }} .page {{ width:100%; margin:0; box-shadow:none; }} header, .score {{ print-color-adjust:exact; -webkit-print-color-adjust:exact; }} main {{ padding:25px 30px; }} }}
  </style>
</head>
<body>
  <div class="toolbar"><button type="button" onclick="window.close()">Fechar</button><button type="button" class="primary" onclick="window.print()">Imprimir / Salvar como PDF</button></div>
  <article class="page">
    <header>
      <div class="brand"><span class="brand-mark">CS</span><span>CS Platform</span></div>
      <p class="kicker">Análise econômica</p>
      <h1>Relatório de diagnóstico financeiro</h1>
      <div class="report-meta"><span>{escape(report_label)}</span><span>Referência: {escape(reference_text)}</span></div>
    </header>
    <main>
      <section class="client"><div><span>Cliente</span><strong>{escape(client.full_name)}</strong></div><div><span>CPF</span><strong>{cpf_display(client.cpf)}</strong></div></section>
      <section class="metrics">
        <div class="metric"><span>Renda total</span><strong>R$ {brl(data.get('total_income'))}</strong></div>
        <div class="metric"><span>Despesas essenciais</span><strong>R$ {brl(data.get('total_expenses'))}</strong></div>
        <div class="metric"><span>Parcelas mensais</span><strong>R$ {brl(data.get('total_installments'))}</strong></div>
        <div class="metric"><span>Saldo de dívidas</span><strong>R$ {brl(data.get('total_debt_balance'))}</strong></div>
        <div class="metric"><span>Renda disponível</span><strong>R$ {brl(data.get('disposable_income'))}</strong></div>
      </section>
      <section class="section"><h2>Comprometimento da renda</h2><div class="bar"><span style="width:{width:.2f}%"></span></div><div class="commitment"><span>Percentual destinado às parcelas</span><strong>{str(commitment.quantize(Decimal('0.01'))).replace('.', ',')}%</strong></div></section>
      <section class="section score"><div class="score-number">{escape(str(data.get('eligibility_score', 0)))}<small>pontos de 100</small></div><div><strong>{escape(str(data.get('eligibility_result') or 'Não informado'))}</strong><p>Indicador preliminar sujeito à análise documental e jurídica.</p></div></section>
      <section class="section"><h2>Conclusão econômica</h2><div class="conclusion"><p>{escape(str(data.get('economic_conclusion') or 'Sem conclusão registrada.'))}</p></div></section>
      <section class="section"><h2>Pontos de atenção</h2><ul>{alerts_html}</ul></section>
      <div class="notice">Este relatório é preliminar e não substitui a revisão documental, contábil ou jurídica realizada por profissional responsável.</div>
      <div class="signatures"><div class="signature">Responsável pela análise</div><div class="signature">Cliente</div></div>
    </main>
    <footer>CS Platform — Gestão jurídica inteligente</footer>
  </article>
</body>
</html>"""


def economic_report(client, data: dict) -> str:
    return _render_report(client, data)


def saved_economic_report(client, diagnosis) -> str:
    data = {
        "total_income": diagnosis.total_income,
        "total_expenses": diagnosis.total_expenses,
        "total_debt_balance": diagnosis.total_debt_balance,
        "total_installments": diagnosis.total_installments,
        "disposable_income": diagnosis.disposable_income,
        "commitment_percentage": diagnosis.commitment_percentage,
        "eligibility_score": diagnosis.eligibility_score,
        "eligibility_result": diagnosis.eligibility_result,
        "economic_conclusion": diagnosis.economic_conclusion,
        "legal_alerts": diagnosis.legal_alerts,
    }
    return _render_report(
        client,
        data,
        version=diagnosis.version,
        saved_at=diagnosis.created_at,
    )
