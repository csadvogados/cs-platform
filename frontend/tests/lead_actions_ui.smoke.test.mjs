import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const index = await readFile(new URL("../index.html", import.meta.url), "utf8");
const app = await readFile(new URL("../assets/app.js", import.meta.url), "utf8");
const styles = await readFile(new URL("../assets/styles.css", import.meta.url), "utf8");

test("próxima ação usa formulário próprio com calendário", () => {
  assert.match(index, /id="lead-task-dialog"/);
  assert.match(index, /name="due_date" type="date"/);
  assert.match(app, /openLeadTaskDialog/);
  assert.match(app, /due_date\.min = localDateValue/);
  assert.match(app, /\/tasks`/);
});

test("funil mantém margem e alinhamento ao rolar", () => {
  assert.match(styles, /\.lead-kanban[^}]+scroll-padding-inline:12px/);
  assert.match(styles, /\.lead-column[^}]+scroll-snap-align:start/);
});

test("proposta comercial identifica o lead e aparece na timeline", () => {
  assert.match(index, /id="lead-proposal-dialog"/);
  assert.match(index, /name="success_percentage"/);
  assert.match(index, /name="valid_until" type="date"/);
  assert.match(app, /openLeadProposalDialog/);
  assert.match(app, /timeline\.proposals/);
  assert.match(app, /Proposta salva e vinculada ao lead/);
  assert.match(index, /id="lead-proposal-error"/);
  assert.match(app, /dialog-toast-region/);
  assert.match(styles, /\.dialog-toast-region/);
  assert.match(app, /Não foi possível atualizar:/);
  assert.match(app, /name:"CRM"/);
});

test("conversão atualiza imediatamente o cartão do lead", () => {
  assert.match(app, /Object\.assign\(current, result\.lead\)/);
  assert.match(app, /current\.status = "CONVERTIDO"/);
  assert.match(app, /movido para Convertido/);
});

test("lead convertido pode abrir o caso CS Recupera posteriormente", () => {
  assert.match(app, /data-recovery-lead/);
  assert.match(app, /createRecoveryCaseFromLead/);
  assert.match(app, /Caso CS Recupera criado e vinculado ao cliente/);
});

test("notificação de lead abre diretamente o detalhe no funil", () => {
  assert.match(app, /startsWith\("lead:"\)/);
  assert.match(app, /await openLeadDetail\(leadId\)/);
  assert.match(app, /lead: "◆"/);
});

test("acompanhamento operacional exibe pendências e conclui próximas ações", () => {
  assert.match(app, /Ações atrasadas/);
  assert.match(app, /Propostas vencendo/);
  assert.match(app, /Sem próxima ação/);
  assert.match(app, /data-complete-lead-task/);
  assert.match(app, /Próxima ação concluída/);
});

test("agenda e supervisão incluem a operação diária dos leads", () => {
  assert.match(index, /value="lead_task">Próximas ações de leads/);
  assert.match(index, /id="lead-distribute"/);
  assert.match(index, /id="lead-team-body"/);
  assert.match(app, /\/api\/v1\/leads\/analytics\/team/);
  assert.match(app, /\/api\/v1\/leads\/distribution/);
  assert.match(app, /data-agenda-complete-lead-task/);
});

test("cadastro de lead usa envio assíncrono com retorno visível", () => {
  assert.match(index, /<form id="lead-form">/);
  assert.match(app, /setBusy\(button, true, "Salvando…"\)/);
  assert.match(app, /Lead salvo, mas a tela não foi atualizada/);
});

test("proposta aceita gera contrato com aprovação e assinatura manual", () => {
  assert.match(app, /data-create-contract/);
  assert.match(app, /data-contract-status/);
  assert.match(app, /Gerar contrato/);
  assert.match(app, /Registrar assinatura/);
  assert.match(app, /openLeadContractDocument/);
  assert.match(index, /id="contract-signature-dialog"/);
  assert.match(index, /Confirmar assinatura/);
  assert.doesNotMatch(app, /window\.prompt\("Informe a referência da assinatura/);
});

test("central de contratos permite acompanhar, filtrar e abrir documentos", () => {
  assert.match(index, /data-view="contracts"/);
  assert.match(index, /id="view-contracts"/);
  assert.match(index, /id="contract-status-filter"/);
  assert.match(app, /\/api\/v1\/contracts\/summary/);
  assert.match(app, /data-contract-open-lead/);
  assert.match(app, /data-contract-document/);
});

test("envio de contrato registra canal, destinatário, prazo e reenvio", () => {
  assert.match(index, /id="contract-delivery-dialog"/);
  assert.match(index, /name="signature_due_at" type="date"/);
  assert.match(index, /id="contract-overdue"/);
  assert.match(app, /data-send-contract/);
  assert.match(app, /\/deliveries`/);
  assert.match(app, /Registrar reenvio/);
  assert.match(app, /Envio registrado no histórico do contrato/);
});

test("modelos configuráveis preenchem e geram contratos pelo serviço", () => {
  assert.match(index, /id="contract-template-dialog"/);
  assert.match(index, /\{\{cliente_nome\}\}/);
  assert.match(index, /id="contract-generation-dialog"/);
  assert.match(app, /\/api\/v1\/contracts\/templates/);
  assert.match(app, /openContractGenerationDialog/);
  assert.match(app, /template_id:templateId/);
  assert.match(index, /id="contract-template-delete-dialog"/);
  assert.match(app, /contract-template-delete-form/);
  assert.doesNotMatch(app, /window\.confirm\("Excluir este modelo de contrato/);
});

test("timeline permite decidir proposta com transição auditada pela API", () => {
  assert.match(app, /data-proposal-status="ACEITA"/);
  assert.match(app, /data-proposal-status="RECUSADA"/);
  assert.match(app, /updateLeadProposalStatus/);
});

test("conversão mostra duplicidades antes de criar o cliente", () => {
  assert.match(index, /id="lead-conversion-dialog"/);
  assert.match(app, /\/duplicates`/);
  assert.match(app, /confirm_duplicate_client_id/);
  assert.match(app, /Criar novo cliente/);
  assert.match(styles, /\.conversion-summary > \*[^}]+overflow-wrap:anywhere/);
  assert.match(styles, /\.duplicate-option strong,\.duplicate-option small[^}]+overflow-wrap:anywhere/);
});

test("perda do lead usa formulário com motivos legíveis", () => {
  assert.match(index, /id="lead-lost-dialog"/);
  assert.match(index, /Contratou outro advogado/);
  assert.match(app, /Lead movido para Perdido com o motivo registrado/);
  assert.doesNotMatch(app, /Motivo da perda: SEM_INTERESSE/);
});
