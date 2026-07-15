from html import escape

def economic_report(client, d):
    alerts = ''.join(f'<li>{escape(a)}</li>' for a in d['legal_alerts']) or '<li>Sem alertas adicionais.</li>'
    width = min(float(d['commitment_percentage']), 100)
    return f"""<!doctype html><html lang='pt-br'><head><meta charset='utf-8'><title>Parecer Econômico</title>
<style>body{{font-family:Arial;max-width:900px;margin:30px auto;line-height:1.5}}.cards{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}.card{{border:1px solid #ddd;border-radius:10px;padding:14px}}.bar{{height:22px;background:#e5e7eb;border-radius:12px;overflow:hidden}}.bar span{{display:block;height:100%;background:#b58b2a}}.notice{{background:#eff6ff;border-left:5px solid #2563eb;padding:14px}}@media print{{button{{display:none}}}}</style></head><body>
<button onclick='window.print()'>Imprimir / Salvar PDF</button><h1>PARECER ECONÔMICO INICIAL — CS RECUPERA</h1>
<p><b>Cliente:</b> {escape(client.full_name)} | <b>CPF:</b> {escape(client.cpf)}</p>
<div class='cards'><div class='card'><b>Renda</b><br>R$ {d['total_income']:.2f}</div><div class='card'><b>Despesas</b><br>R$ {d['total_expenses']:.2f}</div><div class='card'><b>Parcelas</b><br>R$ {d['total_installments']:.2f}</div><div class='card'><b>Saldo</b><br>R$ {d['disposable_income']:.2f}</div></div>
<h2>Comprometimento</h2><div class='bar'><span style='width:{width}%'></span></div><p>{d['commitment_percentage']:.2f}% da renda.</p>
<h2>Motor de elegibilidade</h2><h1>{d['eligibility_score']}/100</h1><p><b>{escape(d['eligibility_result'])}</b></p>
<h2>Leitura econômica</h2><p>{escape(d['economic_conclusion'])}</p><h2>Pontos de atenção</h2><ul>{alerts}</ul>
<div class='notice'>Análise preliminar sujeita à revisão documental e profissional.</div></body></html>"""
