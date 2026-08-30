import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const index = await readFile(new URL("../index.html", import.meta.url), "utf8");
const app = await readFile(new URL("../assets/app.js", import.meta.url), "utf8");
const styles = await readFile(new URL("../assets/styles.css", import.meta.url), "utf8");

test("interface contém os formulários de negociação e proposta", () => {
  assert.match(index, /id="negotiation-form"/);
  assert.match(index, /id="negotiation-offer-form"/);
  assert.match(index, /5\.28\.0-negotiation-engine/);
});

test("interface usa todas as rotas do Negotiation Engine", () => {
  assert.match(app, /\/api\/v1\/negotiations\?client_id=/);
  assert.match(app, /\/offers`/);
  assert.match(app, /\/decision`/);
});

test("interface aplica RBAC e renderiza decisão do motor", () => {
  assert.match(app, /negotiation\.create/);
  assert.match(app, /negotiation\.update/);
  assert.match(app, /negotiation\.approve/);
  assert.match(app, /engineDecisionLabels/);
  assert.match(styles, /\.engine-decision/);
});
