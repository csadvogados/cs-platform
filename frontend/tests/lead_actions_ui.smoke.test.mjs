import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const index = await readFile(new URL("../index.html", import.meta.url), "utf8");
const app = await readFile(new URL("../assets/app.js", import.meta.url), "utf8");
const styles = await readFile(new URL("../assets/styles.css", import.meta.url), "utf8");

test("próxima ação usa formulário próprio com data brasileira", () => {
  assert.match(index, /id="lead-task-dialog"/);
  assert.match(index, /name="due_date"[^>]+placeholder="DD\/MM\/AAAA"/);
  assert.match(app, /openLeadTaskDialog/);
  assert.match(app, /parseBrazilianDateTime/);
  assert.match(app, /\/tasks`/);
});

test("funil mantém margem e alinhamento ao rolar", () => {
  assert.match(styles, /\.lead-kanban[^}]+scroll-padding-inline:12px/);
  assert.match(styles, /\.lead-column[^}]+scroll-snap-align:start/);
});
