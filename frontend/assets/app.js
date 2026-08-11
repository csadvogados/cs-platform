(function () {
  "use strict";

  const API_BASE = String(window.CS_CONFIG?.API_BASE_URL || "").replace(/\/$/, "");
  const state = {
    user: null,
    dashboard: null,
    clients: [],
    crm: { summary: null, contacts: [], opportunities: [], tasks: [] },
    selectedClient: null,
    editingClientId: null,
    financial: { incomes: [], expenses: [], debts: [], creditors: [], diagnosis: null, history: [] },
    editingFinancial: null,
    users: [],
    currentView: "dashboard"
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const loginView = $("#login-view");
  const appShell = $("#app-shell");

  const viewMeta = {
    dashboard: ["VISÃO GERAL", "Painel de operação", "Novo cliente"],
    clients: ["RELACIONAMENTO", "Clientes", "Novo cliente"],
    clientDetail: ["CADASTRO DO CLIENTE", "Detalhes do cliente", "Nova receita"],
    crm: ["DESENVOLVIMENTO DE NEGÓCIOS", "CRM", "Nova oportunidade"],
    users: ["ORGANIZAÇÃO", "Equipe", "Atualizar"],
    settings: ["AMBIENTE", "Configurações", "Verificar API"]
  };

  const stageLabels = {
    lead: "Leads",
    qualified: "Qualificação",
    proposal: "Proposta",
    negotiation: "Negociação",
    won: "Ganha",
    lost: "Perdida"
  };

  const priorityLabels = { low: "Baixa", normal: "Normal", high: "Alta", urgent: "Urgente" };

  const clientStatusLabels = {
    lead: "Potencial cliente",
    triage: "Triagem",
    proposal: "Proposta",
    contracted: "Contratado",
    documents_pending: "Documentos pendentes",
    diagnosis: "Diagnóstico",
    negotiation: "Negociação",
    judicial_review: "Análise judicial",
    judicial: "Judicial",
    agreement: "Acordo",
    closed: "Encerrado",
    cancelled: "Cancelado"
  };

  const debtNatureLabels = {
    consumer: "Dívida de consumo",
    credit_card: "Cartão de crédito",
    overdraft: "Cheque especial",
    personal_loan: "Empréstimo pessoal",
    payroll_loan: "Empréstimo consignado",
    essential_service: "Serviço essencial",
    secured_debt: "Dívida com garantia",
    real_estate_financing: "Financiamento imobiliário",
    rural_credit: "Crédito rural",
    tax: "Dívida tributária",
    alimony: "Pensão alimentícia",
    rent_condo: "Aluguel ou condomínio"
  };

  const financialDefinitions = {
    income: { path: "incomes", collection: "incomes", dialogId: "income-dialog", formId: "income-form", singular: "receita", createTitle: "Nova receita", editTitle: "Editar receita", createButton: "Salvar receita" },
    expense: { path: "expenses", collection: "expenses", dialogId: "expense-dialog", formId: "expense-form", singular: "despesa", createTitle: "Nova despesa", editTitle: "Editar despesa", createButton: "Salvar despesa" },
    debt: { path: "debts", collection: "debts", dialogId: "debt-dialog", formId: "debt-form", singular: "dívida", createTitle: "Nova dívida", editTitle: "Editar dívida", createButton: "Salvar dívida" }
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function initials(name) {
    return String(name || "CS").trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
  }

  function formatCurrency(value) {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(Number(value || 0));
  }

  function formatDate(value, includeTime = false) {
    if (!value) return "Sem data";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Sem data";
    return new Intl.DateTimeFormat("pt-BR", includeTime
      ? { dateStyle: "short", timeStyle: "short" }
      : { dateStyle: "short" }).format(date);
  }

  function normalizeCpf(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function compactObject(object) {
    return Object.fromEntries(Object.entries(object).filter(([, value]) => value !== "" && value !== null && value !== undefined));
  }

  function calculateWeightedPipeline(opportunities) {
    const openStages = new Set(["lead", "qualified", "proposal", "negotiation"]);
    return opportunities
      .filter((item) => openStages.has(String(item.stage || "").toLowerCase()))
      .reduce((total, item) => total + (Number(item.estimated_value || 0) * Number(item.probability || 0) / 100), 0);
  }

  function getTokens() {
    return {
      access: sessionStorage.getItem("cs_access_token"),
      refresh: sessionStorage.getItem("cs_refresh_token")
    };
  }

  function clearSession() {
    sessionStorage.removeItem("cs_access_token");
    sessionStorage.removeItem("cs_refresh_token");
    state.user = null;
  }

  async function readError(response) {
    try {
      const body = await response.json();
      if (Array.isArray(body.detail)) return body.detail.map((item) => item.msg).join(" ");
      return body.detail || body.message || `Erro ${response.status}`;
    } catch {
      return `Erro ${response.status} ao acessar a API.`;
    }
  }

  async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const access = getTokens().access;
    if (access) headers.set("Authorization", `Bearer ${access}`);
    if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");

    let response;
    try {
      response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    } catch {
      throw new Error("Não foi possível conectar à API. Confira a internet e a configuração de CORS no Railway.");
    }

    if (response.status === 401 && path !== "/api/v1/auth/login") {
      clearSession();
      showLogin("Sua sessão expirou. Entre novamente.");
      throw new Error("Sessão expirada.");
    }
    if (!response.ok) throw new Error(await readError(response));
    if (response.status === 204) return null;
    return response.json();
  }

  async function openDiagnosisReport(path, button) {
    const popup = window.open("", "_blank");
    if (!popup) {
      toast("O navegador bloqueou a nova janela. Permita pop-ups para abrir o relatório.", "error");
      return;
    }
    popup.opener = null;
    popup.document.write('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Preparando relatório</title><body style="font-family:Arial;padding:32px">Preparando relatório…</body></html>');
    popup.document.close();
    setBusy(button, true, "Abrindo…");
    try {
      const headers = new Headers();
      const access = getTokens().access;
      if (access) headers.set("Authorization", `Bearer ${access}`);
      const response = await fetch(`${API_BASE}${path}`, { headers });
      if (response.status === 401) {
        clearSession();
        showLogin("Sua sessão expirou. Entre novamente.");
        throw new Error("Sessão expirada.");
      }
      if (!response.ok) throw new Error(await readError(response));
      const html = await response.text();
      popup.document.open();
      popup.document.write(html);
      popup.document.close();
      popup.focus();
    } catch (error) {
      if (!popup.closed) {
        popup.document.open();
        popup.document.write(`<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Erro</title><body style="font-family:Arial;padding:32px"><h1>Não foi possível abrir o relatório</h1><p>${escapeHtml(error.message)}</p></body></html>`);
        popup.document.close();
      }
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function toast(message, type = "success") {
    const element = document.createElement("div");
    element.className = `toast ${type === "error" ? "error" : ""}`;
    element.textContent = message;
    $("#toast-region").appendChild(element);
    window.setTimeout(() => element.remove(), 4500);
  }

  function showLogin(message = "") {
    appShell.hidden = true;
    loginView.hidden = false;
    $("#login-message").textContent = message;
    $("#login-password").value = "";
    window.setTimeout(() => $("#login-email").focus(), 30);
  }

  function showApp() {
    loginView.hidden = true;
    appShell.hidden = false;
    applyUser();
    setView(state.currentView);
  }

  function applyUser() {
    if (!state.user) return;
    const name = state.user.full_name || state.user.email || "Equipe";
    const firstName = name.split(" ")[0];
    $("#sidebar-user-name").textContent = name;
    $("#sidebar-user-role").textContent = state.user.role || "equipe";
    $("#user-initials").textContent = initials(name);
    $("#welcome-name").textContent = firstName;
    $("#settings-user").textContent = name;
    $("#settings-email").textContent = state.user.email || "—";
    $("#settings-role").textContent = state.user.role || "—";
  }

  function setView(view) {
    if (!viewMeta[view]) return;
    state.currentView = view;
    $$(".page-view").forEach((section) => section.classList.toggle("active-view", section.id === `view-${view}`));
    $$(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === (view === "clientDetail" ? "clients" : view)));
    $("#view-kicker").textContent = viewMeta[view][0];
    $("#view-title").textContent = viewMeta[view][1];
    $("#top-action-button").textContent = viewMeta[view][2];
    closeSidebar();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function openDialog(id) {
    const dialog = document.getElementById(id);
    const financialDefinition = Object.values(financialDefinitions).find((definition) => definition.dialogId === id);
    if (financialDefinition && !state.selectedClient) {
      toast("Selecione um cliente antes de registrar dados financeiros.", "error");
      return;
    }
    if (financialDefinition) resetFinancialDialog(id);
    if (id === "client-dialog") resetClientDialog();
    if (["opportunity-dialog", "task-dialog"].includes(id)) {
      try {
        await loadClients();
      } catch (error) {
        toast(error.message || "Não foi possível carregar os clientes.", "error");
        return;
      }
    }
    if (dialog?.showModal) dialog.showModal();
  }

  function closeDialog(dialog) {
    if (dialog?.open) dialog.close();
  }

  function resetClientDialog() {
    const dialog = document.getElementById("client-dialog");
    const form = document.getElementById("client-form");
    if (!dialog || !form) return;
    form.reset();
    state.editingClientId = null;
    form.elements.cpf.readOnly = false;
    const eyebrow = $(".modal-header .eyebrow", dialog);
    const title = $(".modal-header h2", dialog);
    const submit = $('button[type="submit"]', form);
    if (eyebrow) eyebrow.textContent = "NOVO REGISTRO";
    if (title) title.textContent = "Cadastrar cliente";
    if (submit) {
      submit.textContent = "Salvar cliente";
      delete submit.dataset.originalLabel;
    }
  }

  function resetFinancialDialog(dialogId) {
    const definition = Object.values(financialDefinitions).find((item) => item.dialogId === dialogId);
    if (!definition) return;
    const dialog = document.getElementById(definition.dialogId);
    const form = document.getElementById(definition.formId);
    if (!dialog || !form) return;
    form.reset();
    state.editingFinancial = null;
    const title = $(".modal-header h2", dialog);
    const submit = $('button[type="submit"]', form);
    if (title) title.textContent = definition.createTitle;
    if (submit) {
      submit.textContent = definition.createButton;
      delete submit.dataset.originalLabel;
    }
  }

  function openSidebar() {
    $("#sidebar").classList.add("open");
    $("#sidebar-scrim").hidden = false;
  }

  function closeSidebar() {
    $("#sidebar").classList.remove("open");
    $("#sidebar-scrim").hidden = true;
  }

  function setBusy(button, busy, label) {
    if (!button) return;
    if (!button.dataset.originalLabel) button.dataset.originalLabel = button.textContent;
    button.disabled = busy;
    button.textContent = busy ? label : button.dataset.originalLabel;
  }

  async function login(event) {
    event.preventDefault();
    const button = $("#login-submit");
    const message = $("#login-message");
    message.textContent = "";
    setBusy(button, true, "Entrando…");
    try {
      const tokens = await api("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: $("#login-email").value.trim(), password: $("#login-password").value })
      });
      sessionStorage.setItem("cs_access_token", tokens.access_token);
      sessionStorage.setItem("cs_refresh_token", tokens.refresh_token);
      state.user = await api("/api/v1/auth/me");
      showApp();
      await refreshAll();
      toast("Acesso realizado com sucesso.");
    } catch (error) {
      message.textContent = error.message === "Incorrect email or password" ? "E-mail ou senha incorretos." : error.message;
    } finally {
      setBusy(button, false);
    }
  }

  async function logout() {
    const refresh = getTokens().refresh;
    try {
      if (refresh) await api("/api/v1/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: refresh }) });
    } catch {
      // A sessão local é encerrada mesmo que o token já tenha expirado no servidor.
    }
    clearSession();
    showLogin("Sessão encerrada com segurança.");
  }

  async function refreshAll(showNotice = false) {
    const button = $("#refresh-button");
    setBusy(button, true, "Atualizando…");
    const loaders = [
      loadDashboard(),
      loadClients(),
      loadCrm(),
      loadUsers(),
      checkHealth()
    ];
    if (state.currentView === "clientDetail" && state.selectedClient) {
      loaders.push(loadClientDetail(state.selectedClient.id));
    }
    const requests = await Promise.allSettled(loaders);
    setBusy(button, false);
    const failed = requests.filter((request) => request.status === "rejected");
    if (failed.length) toast(`${failed.length} área(s) não puderam ser atualizadas.`, "error");
    else if (showNotice) toast("Dados atualizados.");
  }

  async function loadDashboard() {
    state.dashboard = await api("/api/v1/dashboard");
    renderDashboard();
  }

  async function loadClients() {
    const response = await api("/api/v1/clients?limit=100");
    state.clients = Array.isArray(response) ? response : (response.items || []);
    renderClients();
    fillClientSelects();
  }

  async function loadClientDetail(clientId) {
    const client = state.clients.find((item) => String(item.id) === String(clientId));
    if (!client) throw new Error("Cliente não encontrado na base carregada.");
    state.selectedClient = client;

    const paths = [
      `/api/v1/financial/clients/${client.id}/incomes`,
      `/api/v1/financial/clients/${client.id}/expenses`,
      `/api/v1/financial/clients/${client.id}/debts`,
      "/api/v1/financial/creditors",
      `/api/v1/diagnoses/${client.id}/preview`,
      `/api/v1/diagnoses/${client.id}/history?limit=50`
    ];
    const results = await Promise.allSettled(paths.map((path) => api(path)));
    const valueAt = (index, fallback) => results[index].status === "fulfilled" ? results[index].value : fallback;
    state.financial = {
      incomes: Array.isArray(valueAt(0, [])) ? valueAt(0, []) : [],
      expenses: Array.isArray(valueAt(1, [])) ? valueAt(1, []) : [],
      debts: Array.isArray(valueAt(2, [])) ? valueAt(2, []) : [],
      creditors: Array.isArray(valueAt(3, [])) ? valueAt(3, []) : [],
      diagnosis: valueAt(4, null),
      history: Array.isArray(valueAt(5, [])) ? valueAt(5, []) : []
    };
    fillCreditorSelect();
    renderClientDetail();

    const failed = results.filter((result) => result.status === "rejected");
    if (failed.length) {
      const firstMessage = failed[0].reason?.message || "Não foi possível carregar todos os dados financeiros.";
      toast(firstMessage, "error");
    }
  }

  async function openClientDetail(clientId) {
    setView("clientDetail");
    $("#client-detail-content").innerHTML = '<div class="loading-row">Carregando dados do cliente…</div>';
    try {
      await loadClientDetail(clientId);
      $("#view-title").textContent = state.selectedClient.full_name;
    } catch (error) {
      toast(error.message, "error");
      setView("clients");
    }
  }

  async function loadCrm() {
    const [summary, contacts, opportunities, tasks] = await Promise.all([
      api("/api/v1/crm/summary"),
      api("/api/v1/crm/contacts?limit=100"),
      api("/api/v1/crm/opportunities?limit=100"),
      api("/api/v1/crm/tasks?limit=100")
    ]);
    state.crm = {
      summary,
      contacts: Array.isArray(contacts) ? contacts : contacts.items || [],
      opportunities: Array.isArray(opportunities) ? opportunities : opportunities.items || [],
      tasks: Array.isArray(tasks) ? tasks : tasks.items || []
    };
    renderCrm();
    renderDashboard();
  }

  async function loadUsers() {
    const response = await api("/api/v1/users?page=1&page_size=50");
    state.users = Array.isArray(response) ? response : response.items || [];
    renderUsers();
  }

  async function checkHealth() {
    const status = $("#api-status");
    $("#api-address").textContent = API_BASE;
    try {
      const health = await fetch(`${API_BASE}/api/v1/health`).then((response) => {
        if (!response.ok) throw new Error();
        return response.json();
      });
      status.textContent = health.database === "ok" ? "API e banco online" : "API online";
      status.style.color = "#27734f";
    } catch {
      status.textContent = "Não foi possível verificar";
      status.style.color = "#a5413d";
    }
  }

  function renderDashboard() {
    const dashboard = state.dashboard || {};
    const summary = state.crm.summary || {};
    const weightedFromOpportunities = calculateWeightedPipeline(state.crm.opportunities);
    const weighted = state.crm.opportunities.length
      ? weightedFromOpportunities
      : Number(summary.weighted_pipeline_value || 0);
    $("#stat-clients").textContent = dashboard.clients ?? state.clients.length ?? "—";
    $("#stat-diagnoses").textContent = dashboard.diagnoses ?? "—";
    $("#stat-debts").textContent = dashboard.debts ?? "—";
    $("#stat-pipeline").textContent = formatCurrency(summary.open_pipeline_value);
    $("#stat-opportunities").textContent = `${summary.opportunities || 0} oportunidades registradas`;
    $("#weighted-pipeline").textContent = formatCurrency(weighted);
    $("#pending-tasks").textContent = summary.pending_tasks ?? 0;
    $("#overdue-tasks").textContent = summary.overdue_tasks ?? 0;
    const open = Number(summary.open_pipeline_value || 0);
    $("#pipeline-meter").style.width = `${open ? Math.min(100, Math.max(8, (weighted / open) * 100)) : 0}%`;

    const tasks = state.crm.tasks
      .filter((task) => !["completed", "cancelled"].includes(String(task.status).toLowerCase()))
      .sort((a, b) => new Date(a.due_at || "2999-01-01") - new Date(b.due_at || "2999-01-01"))
      .slice(0, 5);
    $("#dashboard-tasks").innerHTML = tasks.length ? tasks.map(taskRow).join("") : '<div class="empty-state">Nenhuma tarefa pendente. Boa notícia.</div>';
  }

  function renderClients() {
    const term = $("#client-search").value.trim().toLocaleLowerCase("pt-BR");
    const clients = state.clients.filter((client) => [client.full_name, client.cpf, client.city, client.email]
      .some((value) => String(value || "").toLocaleLowerCase("pt-BR").includes(term)));
    $("#client-count").textContent = `${clients.length} ${clients.length === 1 ? "cliente" : "clientes"}`;
    $("#clients-table").innerHTML = clients.length ? clients.map((client) => `
      <tr class="client-row" data-client-id="${escapeHtml(client.id)}">
        <td><strong>${escapeHtml(client.full_name)}</strong><br><small>${escapeHtml(client.cpf || "CPF não informado")}</small></td>
        <td>${escapeHtml(client.email || "—")}<br><small>${escapeHtml(client.phone || "")}</small></td>
        <td>${escapeHtml([client.city, client.state].filter(Boolean).join(" / ") || "—")}</td>
        <td><span class="badge ${isClosedClientStatus(client.status) ? "neutral" : ""}">${escapeHtml(clientStatusLabel(client.status))}</span></td>
        <td>${formatDate(client.created_at)}</td>
        <td><button class="text-link" type="button" data-client-detail="${escapeHtml(client.id)}">Ver detalhes</button></td>
      </tr>`).join("") : '<tr><td colspan="6" class="empty-cell">Nenhum cliente encontrado.</td></tr>';
  }

  function fillClientSelects() {
    const options = state.clients.map((client) => `<option value="${escapeHtml(client.id)}">${escapeHtml(client.full_name)}</option>`).join("");
    $("#opportunity-client").innerHTML = `<option value="">Selecione</option>${options}`;
    $("#task-client").innerHTML = `<option value="">Sem cliente vinculado</option>${options}`;
  }

  function fillCreditorSelect() {
    const select = $("#debt-creditor");
    if (!select) return;
    const options = state.financial.creditors.map((creditor) => `<option value="${escapeHtml(creditor.id)}">${escapeHtml(creditor.legal_name)}</option>`).join("");
    select.innerHTML = `<option value="">Sem credor cadastrado</option>${options}`;
  }

  function creditorName(id) {
    return state.financial.creditors.find((creditor) => String(creditor.id) === String(id))?.legal_name || "Credor não informado";
  }

  function debtNatureLabel(value) {
    return debtNatureLabels[String(value || "").toLowerCase()] || value || "Não informada";
  }

  function setSelectValue(select, value, label = value) {
    if (!select) return;
    const normalized = value == null ? "" : String(value);
    if (normalized && !Array.from(select.options).some((option) => option.value === normalized)) {
      select.add(new Option(String(label || normalized), normalized));
    }
    select.value = normalized;
  }

  function clientStatusLabel(value) {
    return clientStatusLabels[String(value || "").toLowerCase()] || value || "Potencial cliente";
  }

  function isClosedClientStatus(value) {
    return ["closed", "cancelled", "inactive"].includes(String(value || "").toLowerCase());
  }

  function diagnosisAlerts(value) {
    const alerts = Array.isArray(value) ? value : String(value || "").split(/\r?\n/);
    return alerts.map((alert) => String(alert).trim()).filter(Boolean);
  }

  function openClientEditor() {
    const client = state.selectedClient;
    const dialog = document.getElementById("client-dialog");
    const form = document.getElementById("client-form");
    if (!client || !dialog || !form) {
      toast("Não foi possível abrir o cadastro do cliente.", "error");
      return;
    }

    resetClientDialog();
    state.editingClientId = client.id;
    form.elements.full_name.value = client.full_name || "";
    form.elements.cpf.value = client.cpf || "";
    form.elements.cpf.readOnly = true;
    form.elements.profession.value = client.profession || "";
    form.elements.email.value = client.email || "";
    form.elements.phone.value = client.phone || "";
    form.elements.city.value = client.city || "";
    form.elements.state.value = client.state || "";
    form.elements.notes.value = client.notes || "";
    setSelectValue(form.elements.status, client.status || "lead", clientStatusLabel(client.status));

    $(".modal-header .eyebrow", dialog).textContent = "CADASTRO DO CLIENTE";
    $(".modal-header h2", dialog).textContent = "Editar cliente";
    const submit = $('button[type="submit"]', form);
    submit.textContent = "Salvar alterações";
    delete submit.dataset.originalLabel;
    dialog.showModal();
  }

  function openFinancialEditor(kind, itemId) {
    const definition = financialDefinitions[kind];
    if (!definition || !state.selectedClient) return;
    const item = state.financial[definition.collection].find((entry) => String(entry.id) === String(itemId));
    const dialog = document.getElementById(definition.dialogId);
    const form = document.getElementById(definition.formId);
    if (!item || !dialog || !form) {
      toast("Não foi possível localizar o registro para edição.", "error");
      return;
    }

    resetFinancialDialog(definition.dialogId);
    state.editingFinancial = { kind, id: item.id };
    const title = $(".modal-header h2", dialog);
    const submit = $('button[type="submit"]', form);
    if (title) title.textContent = definition.editTitle;
    if (submit) {
      submit.textContent = "Salvar alterações";
      delete submit.dataset.originalLabel;
    }

    if (kind === "income") {
      setSelectValue(form.elements.income_type, item.income_type);
      form.elements.description.value = item.description || "";
      form.elements.net_amount.value = item.net_amount ?? "";
      form.elements.recurring.checked = Boolean(item.recurring);
    } else if (kind === "expense") {
      setSelectValue(form.elements.category, item.category);
      form.elements.description.value = item.description || "";
      form.elements.amount.value = item.amount ?? "";
      form.elements.essential.checked = Boolean(item.essential);
      form.elements.recurring.checked = Boolean(item.recurring);
    } else if (kind === "debt") {
      setSelectValue(form.elements.nature, item.nature, debtNatureLabel(item.nature));
      setSelectValue(form.elements.creditor_id, item.creditor_id || "");
      form.elements.new_creditor.value = "";
      form.elements.current_balance.value = item.current_balance ?? "";
      form.elements.monthly_installment.value = item.monthly_installment ?? 0;
      form.elements.overdue.checked = Boolean(item.overdue);
    }
    dialog.showModal();
  }

  function renderClientDetail() {
    const client = state.selectedClient;
    if (!client) return;
    const { incomes, expenses, debts, diagnosis, history } = state.financial;
    const totalIncome = incomes.reduce((total, item) => total + Number(item.net_amount || 0), 0);
    const totalExpenses = expenses.reduce((total, item) => total + Number(item.amount || 0), 0);
    const totalDebt = debts.reduce((total, item) => total + Number(item.current_balance || 0), 0);
    const disposable = totalIncome - totalExpenses;

    $("#client-detail-content").innerHTML = `
      <div class="client-detail-hero">
        <div>
          <button id="back-to-clients" class="text-link back-link" type="button">← Voltar para clientes</button>
          <p class="eyebrow dark">CLIENTE</p>
          <h1>${escapeHtml(client.full_name)}</h1>
          <p>${escapeHtml(client.cpf || "CPF não informado")} · ${escapeHtml(client.email || "E-mail não informado")} · ${escapeHtml(client.phone || "Telefone não informado")}</p>
        </div>
        <div class="button-row"><span class="badge ${isClosedClientStatus(client.status) ? "neutral" : ""}">${escapeHtml(clientStatusLabel(client.status))}</span><button id="edit-client-button" class="secondary-button" type="button">Editar cadastro</button></div>
      </div>

      <div class="client-profile-grid">
        <div><span>Profissão</span><strong>${escapeHtml(client.profession || "Não informada")}</strong></div>
        <div><span>Localização</span><strong>${escapeHtml([client.city, client.state].filter(Boolean).join(" / ") || "Não informada")}</strong></div>
        <div><span>Observações</span><strong>${escapeHtml(client.notes || "Sem observações")}</strong></div>
      </div>

      <div class="financial-summary">
        <article><span>Receita mensal</span><strong>${formatCurrency(totalIncome)}</strong><small>${incomes.length} registro(s)</small></article>
        <article><span>Despesas mensais</span><strong>${formatCurrency(totalExpenses)}</strong><small>${expenses.length} registro(s)</small></article>
        <article><span>Renda disponível</span><strong class="${disposable < 0 ? "danger-text" : ""}">${formatCurrency(disposable)}</strong><small>Receitas menos despesas</small></article>
        <article class="accent"><span>Saldo de dívidas</span><strong>${formatCurrency(totalDebt)}</strong><small>${debts.length} registro(s)</small></article>
      </div>

      <div class="detail-grid">
        <section class="panel detail-panel">
          <div class="panel-header"><div><p class="eyebrow dark">ENTRADAS</p><h3>Receitas</h3></div><button class="secondary-button" type="button" data-open-dialog="income-dialog">Nova receita</button></div>
          <div class="detail-list">${incomes.length ? incomes.map((item) => `<article><span><strong>${escapeHtml(item.income_type)}</strong><small>${escapeHtml(item.description || (item.recurring ? "Receita recorrente" : "Receita eventual"))}</small></span><div class="detail-item-actions"><strong>${formatCurrency(item.net_amount)}</strong><span class="financial-actions"><button class="edit-button" type="button" data-edit-financial="income" data-edit-id="${escapeHtml(item.id)}">Editar</button><button class="delete-button" type="button" data-delete-financial="income" data-delete-id="${escapeHtml(item.id)}">Apagar</button></span></div></article>`).join("") : '<div class="empty-state">Nenhuma receita cadastrada.</div>'}</div>
        </section>

        <section class="panel detail-panel">
          <div class="panel-header"><div><p class="eyebrow dark">SAÍDAS</p><h3>Despesas</h3></div><button class="secondary-button" type="button" data-open-dialog="expense-dialog">Nova despesa</button></div>
          <div class="detail-list">${expenses.length ? expenses.map((item) => `<article><span><strong>${escapeHtml(item.category)}</strong><small>${escapeHtml(item.description || (item.essential ? "Despesa essencial" : "Despesa não essencial"))}</small></span><div class="detail-item-actions"><strong>${formatCurrency(item.amount)}</strong><span class="financial-actions"><button class="edit-button" type="button" data-edit-financial="expense" data-edit-id="${escapeHtml(item.id)}">Editar</button><button class="delete-button" type="button" data-delete-financial="expense" data-delete-id="${escapeHtml(item.id)}">Apagar</button></span></div></article>`).join("") : '<div class="empty-state">Nenhuma despesa cadastrada.</div>'}</div>
        </section>
      </div>

      <section class="panel debt-panel">
        <div class="panel-header"><div><p class="eyebrow dark">ENDIVIDAMENTO</p><h3>Dívidas</h3></div><button class="secondary-button" type="button" data-open-dialog="debt-dialog">Nova dívida</button></div>
        <div class="table-wrap compact-table">
          <table><thead><tr><th>Natureza</th><th>Credor</th><th>Saldo atual</th><th>Parcela mensal</th><th>Situação</th><th>Ações</th></tr></thead>
          <tbody>${debts.length ? debts.map((item) => `<tr><td>${escapeHtml(debtNatureLabel(item.nature))}</td><td>${escapeHtml(creditorName(item.creditor_id))}</td><td>${formatCurrency(item.current_balance)}</td><td>${formatCurrency(item.monthly_installment)}</td><td><span class="badge ${item.overdue ? "danger" : ""}">${item.overdue ? "Em atraso" : "Em dia"}</span></td><td><span class="financial-actions"><button class="edit-button" type="button" data-edit-financial="debt" data-edit-id="${escapeHtml(item.id)}">Editar</button><button class="delete-button" type="button" data-delete-financial="debt" data-delete-id="${escapeHtml(item.id)}">Apagar</button></span></td></tr>`).join("") : '<tr><td colspan="6" class="empty-cell">Nenhuma dívida cadastrada.</td></tr>'}</tbody></table>
        </div>
      </section>

      <section class="panel diagnosis-panel">
        <div class="panel-header"><div><p class="eyebrow dark">ANÁLISE ECONÔMICA</p><h3>Diagnóstico financeiro</h3></div><div class="button-row"><button id="open-current-report" class="secondary-button" type="button">Abrir relatório</button><button id="refresh-diagnosis" class="secondary-button" type="button">Atualizar prévia</button><button id="save-diagnosis" class="primary-button" type="button">Salvar diagnóstico</button></div></div>
        ${diagnosis ? `<div class="diagnosis-grid">
          <article class="diagnosis-score"><span>Pontuação</span><strong>${escapeHtml(diagnosis.eligibility_score)}</strong><small>${escapeHtml(diagnosis.eligibility_result)}</small></article>
          <dl class="definition-list"><div><dt>Renda total</dt><dd>${formatCurrency(diagnosis.total_income)}</dd></div><div><dt>Despesas</dt><dd>${formatCurrency(diagnosis.total_expenses)}</dd></div><div><dt>Parcelas mensais</dt><dd>${formatCurrency(diagnosis.total_installments)}</dd></div><div><dt>Comprometimento</dt><dd>${Number(diagnosis.commitment_percentage || 0).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</dd></div></dl>
          <div class="diagnosis-conclusion"><strong>Conclusão econômica</strong><p>${escapeHtml(diagnosis.economic_conclusion)}</p>${diagnosisAlerts(diagnosis.legal_alerts).length ? `<ul>${diagnosisAlerts(diagnosis.legal_alerts).map((alert) => `<li>${escapeHtml(alert)}</li>`).join("")}</ul>` : '<p class="muted">Sem alertas jurídicos nesta prévia.</p>'}</div>
        </div>` : '<div class="empty-state">Não foi possível gerar a prévia do diagnóstico.</div>'}
      </section>

      <section class="panel diagnosis-history-panel">
        <div class="panel-header"><div><p class="eyebrow dark">REGISTROS SALVOS</p><h3>Histórico de diagnósticos</h3></div><span class="result-count">${history.length} ${history.length === 1 ? "versão" : "versões"}</span></div>
        <div class="diagnosis-history-list">${history.length ? history.map((item) => {
          const alerts = diagnosisAlerts(item.legal_alerts);
          return `<details class="diagnosis-history-item">
            <summary><span><strong>Versão ${escapeHtml(item.version)}</strong><small>${escapeHtml(formatDate(item.created_at, true))}</small></span><span class="history-result">${escapeHtml(item.eligibility_result)}</span><span class="history-score">${escapeHtml(item.eligibility_score)} pontos</span></summary>
            <div class="diagnosis-history-content">
              <dl class="definition-list"><div><dt>Renda total</dt><dd>${formatCurrency(item.total_income)}</dd></div><div><dt>Despesas</dt><dd>${formatCurrency(item.total_expenses)}</dd></div><div><dt>Saldo de dívidas</dt><dd>${formatCurrency(item.total_debt_balance)}</dd></div><div><dt>Parcelas</dt><dd>${formatCurrency(item.total_installments)}</dd></div><div><dt>Renda disponível</dt><dd>${formatCurrency(item.disposable_income)}</dd></div><div><dt>Comprometimento</dt><dd>${Number(item.commitment_percentage || 0).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</dd></div></dl>
              <div class="diagnosis-conclusion"><strong>Conclusão registrada</strong><p>${escapeHtml(item.economic_conclusion)}</p>${alerts.length ? `<ul>${alerts.map((alert) => `<li>${escapeHtml(alert)}</li>`).join("")}</ul>` : '<p class="muted">Sem alertas jurídicos nesta versão.</p>'}</div>
              <div class="history-report-row"><button class="secondary-button" type="button" data-open-saved-report="${escapeHtml(item.id)}">Abrir relatório desta versão</button></div>
            </div>
          </details>`;
        }).join("") : '<div class="empty-state">Nenhum diagnóstico foi salvo para este cliente.</div>'}</div>
      </section>`;

    $("#back-to-clients").addEventListener("click", () => setView("clients"));
    $("#edit-client-button").addEventListener("click", openClientEditor);
    $$("[data-open-dialog]", $("#client-detail-content")).forEach((button) => button.addEventListener("click", () => openDialog(button.dataset.openDialog)));
    $$("[data-edit-financial]", $("#client-detail-content")).forEach((button) => button.addEventListener("click", () => openFinancialEditor(button.dataset.editFinancial, button.dataset.editId)));
    $$("[data-delete-financial]", $("#client-detail-content")).forEach((button) => button.addEventListener("click", () => deleteFinancial(button.dataset.deleteFinancial, button.dataset.deleteId, button)));
    $("#open-current-report")?.addEventListener("click", (event) => openDiagnosisReport(`/api/v1/diagnoses/${client.id}/report`, event.currentTarget));
    $$("[data-open-saved-report]", $("#client-detail-content")).forEach((button) => button.addEventListener("click", () => openDiagnosisReport(`/api/v1/diagnoses/${client.id}/history/${button.dataset.openSavedReport}/report`, button)));
    $("#refresh-diagnosis")?.addEventListener("click", refreshDiagnosis);
    $("#save-diagnosis")?.addEventListener("click", saveDiagnosis);
  }

  function clientName(id) {
    return state.clients.find((client) => String(client.id) === String(id))?.full_name || "Cliente não identificado";
  }

  function taskRow(task) {
    const priority = String(task.priority || "normal").toLowerCase();
    const isOverdue = task.due_at && new Date(task.due_at) < new Date() && !["completed", "cancelled"].includes(String(task.status).toLowerCase());
    return `<div class="list-row">
      <span class="list-icon">${priority === "urgent" ? "!" : "✓"}</span>
      <span><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(task.client_id ? clientName(task.client_id) : priorityLabels[priority] || priority)}</small></span>
      <span class="list-meta ${isOverdue ? "danger-text" : ""}">${escapeHtml(task.due_at ? formatDate(task.due_at, true) : "Sem prazo")}</span>
    </div>`;
  }

  function renderCrm() {
    const summary = state.crm.summary || {};
    $("#crm-contacts-count").textContent = summary.contacts ?? state.crm.contacts.length;
    $("#crm-opportunities-count").textContent = summary.opportunities ?? state.crm.opportunities.length;
    $("#crm-open-value").textContent = formatCurrency(summary.open_pipeline_value);
    $("#crm-pending-count").textContent = summary.pending_tasks ?? 0;

    const boardStages = ["lead", "qualified", "proposal", "negotiation"];
    $("#opportunity-board").innerHTML = boardStages.map((stage) => {
      const opportunities = state.crm.opportunities.filter((item) => item.stage === stage);
      return `<section class="stage-column">
        <div class="stage-header"><strong>${stageLabels[stage]}</strong><span>${opportunities.length}</span></div>
        ${opportunities.length ? opportunities.map((item) => `<article class="opportunity-card">
          <h4>${escapeHtml(item.title)}</h4>
          <p>${escapeHtml(clientName(item.client_id))}</p>
          <p><strong>${formatCurrency(item.estimated_value)}</strong> · ${Number(item.probability || 0)}%</p>
          <p>Previsão: ${formatDate(item.expected_close_date)}</p>
        </article>`).join("") : '<div class="empty-state">Sem oportunidades</div>'}
      </section>`;
    }).join("");

    $("#task-list").innerHTML = state.crm.tasks.length ? state.crm.tasks.map(taskRow).join("") : '<div class="empty-state">Nenhuma tarefa cadastrada.</div>';
    $("#contact-count").textContent = `${state.crm.contacts.length} ${state.crm.contacts.length === 1 ? "contato" : "contatos"}`;
    $("#contact-list").innerHTML = state.crm.contacts.length ? state.crm.contacts.map((contact) => `<article class="contact-card">
      <span class="avatar">${escapeHtml(initials(contact.name))}</span>
      <h4>${escapeHtml(contact.name)}</h4>
      <p>${escapeHtml(contact.position || "Contato comercial")}</p>
      <p>${escapeHtml(contact.email || "E-mail não informado")}</p>
      <p>${escapeHtml(contact.phone || "")}</p>
    </article>`).join("") : '<div class="empty-state">Nenhum contato cadastrado.</div>';
  }

  function renderUsers() {
    $("#user-list").innerHTML = state.users.length ? state.users.map((user) => `<article class="person-row">
      <span class="avatar">${escapeHtml(initials(user.full_name))}</span>
      <div><h4>${escapeHtml(user.full_name)}</h4><p>${escapeHtml(user.email)}</p></div>
      <span>${escapeHtml(user.role || "equipe")}</span>
      <span class="badge ${user.status !== "active" ? "neutral" : ""}">${escapeHtml(user.status || "active")}</span>
    </article>`).join("") : '<div class="empty-state">Nenhum usuário encontrado.</div>';
  }

  async function deleteFinancial(kind, itemId, button) {
    if (!state.selectedClient || !itemId) return;
    const definition = financialDefinitions[kind];
    if (!definition) return;
    const confirmed = window.confirm(`Deseja realmente apagar esta ${definition.singular}? Esta ação não pode ser desfeita.`);
    if (!confirmed) return;

    setBusy(button, true, "Apagando…");
    try {
      await api(`/api/v1/financial/clients/${state.selectedClient.id}/${definition.path}/${itemId}`, { method: "DELETE" });
      await refreshFinancial(`${definition.singular.charAt(0).toUpperCase()}${definition.singular.slice(1)} apagada.`);
    } catch (error) {
      toast(error.message, "error");
      setBusy(button, false);
    }
  }

  async function refreshFinancial(message = "Dados financeiros atualizados.") {
    if (!state.selectedClient) return;
    await loadClientDetail(state.selectedClient.id);
    await Promise.allSettled([loadDashboard(), loadClients()]);
    if (message) toast(message);
  }

  async function submitIncome(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity() || !state.selectedClient) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      data.net_amount = Number(data.net_amount);
      data.recurring = form.elements.recurring.checked;
      const editing = state.editingFinancial?.kind === "income" ? state.editingFinancial : null;
      const suffix = editing ? `/${editing.id}` : "";
      await api(`/api/v1/financial/clients/${state.selectedClient.id}/incomes${suffix}`, { method: editing ? "PUT" : "POST", body: JSON.stringify(data) });
      closeDialog(form.closest("dialog"));
      await refreshFinancial(editing ? "Receita atualizada." : "Receita cadastrada.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function submitExpense(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity() || !state.selectedClient) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      data.amount = Number(data.amount);
      data.essential = form.elements.essential.checked;
      data.recurring = form.elements.recurring.checked;
      const editing = state.editingFinancial?.kind === "expense" ? state.editingFinancial : null;
      const suffix = editing ? `/${editing.id}` : "";
      await api(`/api/v1/financial/clients/${state.selectedClient.id}/expenses${suffix}`, { method: editing ? "PUT" : "POST", body: JSON.stringify(data) });
      closeDialog(form.closest("dialog"));
      await refreshFinancial(editing ? "Despesa atualizada." : "Despesa cadastrada.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function submitDebt(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity() || !state.selectedClient) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      const raw = Object.fromEntries(new FormData(form));
      let creditorId = raw.creditor_id || null;
      if (raw.new_creditor?.trim()) {
        const creditor = await api("/api/v1/financial/creditors", {
          method: "POST",
          body: JSON.stringify({ legal_name: raw.new_creditor.trim() })
        });
        creditorId = creditor.id;
      }
      const data = {
        creditor_id: creditorId,
        nature: raw.nature,
        current_balance: Number(raw.current_balance || 0),
        monthly_installment: Number(raw.monthly_installment || 0),
        overdue: form.elements.overdue.checked
      };
      const editing = state.editingFinancial?.kind === "debt" ? state.editingFinancial : null;
      const suffix = editing ? `/${editing.id}` : "";
      await api(`/api/v1/financial/clients/${state.selectedClient.id}/debts${suffix}`, { method: editing ? "PUT" : "POST", body: JSON.stringify(data) });
      closeDialog(form.closest("dialog"));
      await refreshFinancial(editing ? "Dívida atualizada." : "Dívida cadastrada.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function refreshDiagnosis() {
    if (!state.selectedClient) return;
    const button = $("#refresh-diagnosis");
    setBusy(button, true, "Atualizando…");
    try {
      state.financial.diagnosis = await api(`/api/v1/diagnoses/${state.selectedClient.id}/preview`);
      renderClientDetail();
      toast("Prévia do diagnóstico atualizada.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy($("#refresh-diagnosis"), false);
    }
  }

  async function saveDiagnosis() {
    if (!state.selectedClient) return;
    const button = $("#save-diagnosis");
    setBusy(button, true, "Salvando…");
    try {
      await api(`/api/v1/diagnoses/${state.selectedClient.id}`, { method: "POST" });
      await refreshFinancial("");
      toast("Diagnóstico salvo com sucesso.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy($("#save-diagnosis"), false);
    }
  }

  async function submitClient(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const data = Object.fromEntries(new FormData(form));
    const editingId = state.editingClientId;
    data.cpf = normalizeCpf(data.cpf);
    if (!/^\d{11}$/.test(data.cpf) || /^(\d)\1{10}$/.test(data.cpf)) {
      toast("Informe um CPF com exatamente 11 dígitos válidos.", "error");
      $('[name="cpf"]', form)?.focus();
      return;
    }
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      if (data.state) data.state = data.state.toUpperCase();
      let updatedClient = null;
      if (editingId) {
        const payload = {
          full_name: data.full_name,
          profession: data.profession || null,
          email: data.email || null,
          phone: data.phone || null,
          city: data.city || null,
          state: data.state || null,
          status: data.status || "lead",
          notes: data.notes || null
        };
        updatedClient = await api(`/api/v1/clients/${editingId}`, { method: "PATCH", body: JSON.stringify(payload) });
      } else {
        await api("/api/v1/clients", { method: "POST", body: JSON.stringify(compactObject(data)) });
      }
      closeDialog(form.closest("dialog"));
      await loadClients();
      await loadDashboard();
      if (updatedClient) {
        state.selectedClient = updatedClient;
        renderClientDetail();
        $("#view-title").textContent = updatedClient.full_name;
      }
      toast(editingId ? "Cadastro do cliente atualizado." : "Cliente cadastrado.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function submitContact(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      await api("/api/v1/crm/contacts", { method: "POST", body: JSON.stringify(data) });
      form.reset();
      closeDialog(form.closest("dialog"));
      await loadCrm();
      toast("Contato cadastrado.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function submitOpportunity(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      if (data.estimated_value) data.estimated_value = Number(data.estimated_value);
      if (data.probability) data.probability = Number(data.probability);
      await api("/api/v1/crm/opportunities", { method: "POST", body: JSON.stringify(data) });
      form.reset();
      closeDialog(form.closest("dialog"));
      await loadCrm();
      toast("Oportunidade cadastrada.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function submitTask(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      if (data.due_at) data.due_at = new Date(data.due_at).toISOString();
      await api("/api/v1/crm/tasks", { method: "POST", body: JSON.stringify(data) });
      form.reset();
      closeDialog(form.closest("dialog"));
      await loadCrm();
      toast("Tarefa cadastrada.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function handleTopAction() {
    const actions = {
      dashboard: () => openDialog("client-dialog"),
      clients: () => openDialog("client-dialog"),
      clientDetail: () => openDialog("income-dialog"),
      crm: () => openDialog("opportunity-dialog"),
      users: () => refreshAll(true),
      settings: () => checkHealth().then(() => toast("Verificação concluída."))
    };
    actions[state.currentView]?.();
  }

  function wireEvents() {
    $("#login-form").addEventListener("submit", login);
    $("#logout-button").addEventListener("click", logout);
    $("#refresh-button").addEventListener("click", () => refreshAll(true));
    $("#top-action-button").addEventListener("click", handleTopAction);
    $("#menu-button").addEventListener("click", openSidebar);
    $("#sidebar-scrim").addEventListener("click", closeSidebar);
    $("#client-search").addEventListener("input", renderClients);
    $("#client-form").addEventListener("submit", submitClient);
    $("#contact-form").addEventListener("submit", submitContact);
    $("#opportunity-form").addEventListener("submit", submitOpportunity);
    $("#task-form").addEventListener("submit", submitTask);
    $("#income-form").addEventListener("submit", submitIncome);
    $("#expense-form").addEventListener("submit", submitExpense);
    $("#debt-form").addEventListener("submit", submitDebt);
    $("#clients-table").addEventListener("click", (event) => {
      const button = event.target.closest("[data-client-detail]");
      if (button) openClientDetail(button.dataset.clientDetail);
    });
    $("#toggle-password").addEventListener("click", () => {
      const input = $("#login-password");
      const visible = input.type === "text";
      input.type = visible ? "password" : "text";
      $("#toggle-password").textContent = visible ? "Mostrar" : "Ocultar";
    });
    $$("[data-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
    $$("[data-view-link]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.viewLink)));
    $$("[data-open-dialog]").forEach((button) => button.addEventListener("click", () => openDialog(button.dataset.openDialog)));
    $$("[data-close-dialog]").forEach((button) => button.addEventListener("click", () => closeDialog(button.closest("dialog"))));
    $("#client-dialog").addEventListener("close", resetClientDialog);
    Object.values(financialDefinitions).forEach((definition) => {
      document.getElementById(definition.dialogId)?.addEventListener("close", () => resetFinancialDialog(definition.dialogId));
    });
    $$(".crm-tab").forEach((button) => button.addEventListener("click", () => {
      $$(".crm-tab").forEach((tab) => tab.classList.toggle("active", tab === button));
      $$(".crm-tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === `crm-${button.dataset.crmTab}`));
    }));
  }

  async function boot() {
    $("#today-date").textContent = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "long" }).format(new Date());
    $("#api-address").textContent = API_BASE || "Não configurada";
    wireEvents();
    if (!API_BASE) {
      showLogin("A API ainda não foi configurada no arquivo config.js.");
      return;
    }
    if (!getTokens().access) {
      showLogin();
      checkHealth();
      return;
    }
    try {
      state.user = await api("/api/v1/auth/me");
      showApp();
      await refreshAll();
    } catch {
      showLogin("Entre novamente para continuar.");
    }
  }

  boot();
})();
