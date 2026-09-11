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
});

test("perda do lead usa formulário com motivos legíveis", () => {
  assert.match(index, /id="lead-lost-dialog"/);
  assert.match(index, /Contratou outro advogado/);
  assert.match(app, /Lead movido para Perdido com o motivo registrado/);
  assert.doesNotMatch(app, /Motivo da perda: SEM_INTERESSE/);
});
