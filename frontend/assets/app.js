(function () {
  "use strict";

  const API_BASE = String(window.CS_CONFIG?.API_BASE_URL || "").replace(/\/$/, "");
  const state = {
    user: null,
    dashboard: null,
    clients: [],
    crm: { summary: null, contacts: [], opportunities: [], tasks: [] },
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
    $$(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
    $("#view-kicker").textContent = viewMeta[view][0];
    $("#view-title").textContent = viewMeta[view][1];
    $("#top-action-button").textContent = viewMeta[view][2];
    closeSidebar();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function openDialog(id) {
    const dialog = document.getElementById(id);
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
    const requests = await Promise.allSettled([
      loadDashboard(),
      loadClients(),
      loadCrm(),
      loadUsers(),
      checkHealth()
    ]);
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
      <tr>
        <td><strong>${escapeHtml(client.full_name)}</strong><br><small>${escapeHtml(client.cpf || "CPF não informado")}</small></td>
        <td>${escapeHtml(client.email || "—")}<br><small>${escapeHtml(client.phone || "")}</small></td>
        <td>${escapeHtml([client.city, client.state].filter(Boolean).join(" / ") || "—")}</td>
        <td><span class="badge ${client.status === "inactive" ? "neutral" : ""}">${escapeHtml(client.status || "lead")}</span></td>
        <td>${formatDate(client.created_at)}</td>
      </tr>`).join("") : '<tr><td colspan="5" class="empty-cell">Nenhum cliente encontrado.</td></tr>';
  }

  function fillClientSelects() {
    const options = state.clients.map((client) => `<option value="${escapeHtml(client.id)}">${escapeHtml(client.full_name)}</option>`).join("");
    $("#opportunity-client").innerHTML = `<option value="">Selecione</option>${options}`;
    $("#task-client").innerHTML = `<option value="">Sem cliente vinculado</option>${options}`;
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

  async function submitClient(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const data = Object.fromEntries(new FormData(form));
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
      await api("/api/v1/clients", { method: "POST", body: JSON.stringify(compactObject(data)) });
      form.reset();
      closeDialog(form.closest("dialog"));
      await loadClients();
      await loadDashboard();
      toast("Cliente cadastrado.");
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
