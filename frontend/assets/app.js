(function () {
  "use strict";

  const API_BASE = String(window.CS_CONFIG?.API_BASE_URL || "").replace(/\/$/, "");
  const state = {
    user: null,
    dashboard: null,
    clients: [],
    crm: { summary: null, contacts: [], opportunities: [], tasks: [], interactions: [] },
    crmFilters: { search: "", taskStatus: "all", priority: "all", interactionType: "all" },
    editingCrm: { contact: null, opportunity: null, task: null, interaction: null },
    selectedClient: null,
    editingClientId: null,
    clientImport: { filename: "", clients: [], preview: null },
    financial: { incomes: [], expenses: [], debts: [], creditors: [], diagnosis: null, history: [] },
    editingFinancial: null,
    editingUserId: null,
    users: [],
    organization: null,
    sessions: [],
    audit: {
      items: [],
      total: 0,
      page: 1,
      pageSize: 25,
      pages: 0,
      filters: { search: "", entityType: "all", action: "all", userId: "all", dateFrom: "", dateTo: "" }
    },
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
    audit: ["CONTROLE E SEGURANÇA", "Histórico de atividades", "Atualizar"],
    settings: ["SEGURANÇA E CONTA", "Configurações", "Atualizar"]
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

  const taskStatusLabels = {
    pending: "Pendente",
    in_progress: "Em andamento",
    completed: "Concluída",
    cancelled: "Cancelada"
  };

  const interactionTypeLabels = {
    call: "Ligação",
    email: "E-mail",
    meeting: "Reunião",
    message: "Mensagem",
    note: "Observação",
    other: "Outro atendimento"
  };

  const userRoleLabels = {
    admin: "Administrador",
    supervisor: "Supervisor",
    advogado: "Advogado",
    negociador: "Negociador",
    financeiro: "Financeiro",
    atendimento: "Atendimento"
  };

  const userStatusLabels = { active: "Ativo", inactive: "Inativo" };

  const auditEntityLabels = {
    auth: "Acesso",
    user: "Equipe",
    role: "Perfil de acesso",
    invitation: "Convite",
    session: "Sessão",
    organization: "Organização",
    client: "Cliente",
    income: "Receita",
    expense: "Despesa",
    creditor: "Credor",
    debt: "Dívida",
    diagnosis: "Diagnóstico",
    crm_contact: "Contato CRM",
    crm_interaction: "Atendimento",
    crm_opportunity: "Oportunidade",
    crm_task: "Tarefa"
  };

  const auditActionLabels = {
    login: "Entrou",
    logout: "Saiu",
    change_password: "Alterou a senha",
    create: "Criou",
    update: "Atualizou",
    delete: "Apagou",
    export: "Exportou",
    import: "Importou",
    block: "Desativou",
    unblock: "Reativou",
    complete: "Concluiu",
    revoke: "Encerrou sessão",
    revoke_all: "Encerrou todas as sessões",
    accept: "Aceitou convite"
  };

  const auditDetailLabels = {
    name: "Nome",
    full_name: "Nome",
    email: "E-mail",
    title: "Título",
    subject: "Assunto",
    role: "Perfil",
    status: "Status",
    stage: "Etapa",
    priority: "Prioridade",
    amount: "Valor",
    estimated_value: "Valor estimado",
    current_balance: "Saldo atual",
    monthly_installment: "Parcela mensal",
    nature: "Natureza",
    legal_name: "Razão social",
    trade_name: "Nome de apresentação",
    version: "Versão",
    eligibility_score: "Pontuação",
    eligibility_result: "Resultado",
    count: "Quantidade",
    query: "Pesquisa",
    source_filename: "Arquivo"
  };

  const crmDefinitions = {
    contact: { collection: "contacts", dialogId: "contact-dialog", formId: "contact-form", singular: "contato", createTitle: "Novo contato", editTitle: "Editar contato", createButton: "Salvar contato" },
    opportunity: { collection: "opportunities", dialogId: "opportunity-dialog", formId: "opportunity-form", singular: "oportunidade", createTitle: "Nova oportunidade", editTitle: "Editar oportunidade", createButton: "Salvar oportunidade" },
    task: { collection: "tasks", dialogId: "task-dialog", formId: "task-form", singular: "tarefa", createTitle: "Nova tarefa", editTitle: "Editar tarefa", createButton: "Salvar tarefa" },
    interaction: { collection: "interactions", dialogId: "interaction-dialog", formId: "interaction-form", singular: "atendimento", createTitle: "Novo atendimento", editTitle: "", createButton: "Salvar atendimento" }
  };

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

  function sessionDevice(userAgent) {
    const value = String(userAgent || "");
    if (!value) return "Dispositivo não identificado";
    const browser = value.includes("Edg/") ? "Microsoft Edge"
      : value.includes("Firefox/") ? "Firefox"
        : value.includes("Chrome/") ? "Google Chrome"
          : value.includes("Safari/") ? "Safari"
            : "Navegador";
    const system = value.includes("Windows") ? "Windows"
      : value.includes("Android") ? "Android"
        : /iPhone|iPad/.test(value) ? "iOS"
          : value.includes("Mac OS") ? "macOS"
            : value.includes("Linux") ? "Linux"
              : "dispositivo desconhecido";
    return `${browser} em ${system}`;
  }

  function sessionIsActive(session) {
    return !session.revoked_at && new Date(session.expires_at).getTime() > Date.now();
  }

  function normalizeCpf(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function compactObject(object) {
    return Object.fromEntries(Object.entries(object).filter(([, value]) => value !== "" && value !== null && value !== undefined));
  }

  function matchesCrmSearch(...values) {
    const term = state.crmFilters.search.trim().toLocaleLowerCase("pt-BR");
    if (!term) return true;
    return values.some((value) => String(value || "").toLocaleLowerCase("pt-BR").includes(term));
  }

  function canManageUsers() {
    return String(state.user?.role || "").toLowerCase() === "admin";
  }

  function canUpdateOrganization() {
    return Boolean(state.user?.is_superuser)
      || (state.user?.permissions || []).includes("organization.update");
  }

  function canViewAudit() {
    return Boolean(state.user?.is_superuser)
      || (state.user?.permissions || []).includes("audit.read");
  }

  function canExportClients() {
    return Boolean(state.user?.is_superuser)
      || (state.user?.permissions || []).includes("client.export");
  }

  function canImportClients() {
    const permissions = state.user?.permissions || [];
    return Boolean(state.user?.is_superuser)
      || (permissions.includes("client.create") && permissions.includes("client.export"));
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
    $("#settings-role").textContent = userRoleLabels[state.user.role] || state.user.role || "—";
    $("#password-security-warning").hidden = !state.user.must_change_password;
    $("#audit-nav-item").hidden = !canViewAudit();
    $("#export-clients-button").hidden = !canExportClients();
    $("#import-clients-button").hidden = !canImportClients();
  }

  function setView(view) {
    if (view === "audit" && !canViewAudit()) view = "dashboard";
    if (!viewMeta[view]) return;
    state.currentView = view;
    $$(".page-view").forEach((section) => section.classList.toggle("active-view", section.id === `view-${view}`));
    $$(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === (view === "clientDetail" ? "clients" : view)));
    $("#view-kicker").textContent = viewMeta[view][0];
    $("#view-title").textContent = viewMeta[view][1];
    $("#top-action-button").textContent = viewMeta[view][2];
    $("#top-action-button").hidden = view === "audit";
    closeSidebar();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function openDialog(id) {
    const dialog = document.getElementById(id);
    if (id === "user-dialog" && !canManageUsers()) {
      toast("Somente administradores podem cadastrar membros.", "error");
      return;
    }
    if (id === "client-import-dialog" && !canImportClients()) {
      toast("Seu perfil não possui permissão para importar clientes.", "error");
      return;
    }
    const financialDefinition = Object.values(financialDefinitions).find((definition) => definition.dialogId === id);
    const crmDefinition = Object.values(crmDefinitions).find((definition) => definition.dialogId === id);
    if (financialDefinition && !state.selectedClient) {
      toast("Selecione um cliente antes de registrar dados financeiros.", "error");
      return;
    }
    if (financialDefinition) resetFinancialDialog(id);
    if (crmDefinition) resetCrmDialog(id);
    if (id === "client-dialog") resetClientDialog();
    if (id === "client-import-dialog") resetClientImportDialog();
    if (id === "user-dialog") resetUserDialog();
    if (["opportunity-dialog", "task-dialog", "interaction-dialog"].includes(id)) {
      try {
        await loadClients();
      } catch (error) {
        toast(error.message || "Não foi possível carregar os clientes.", "error");
        return;
      }
    }
    if (id === "interaction-dialog") {
      $("#interaction-form").elements.occurred_at.value = toLocalDateTimeValue(new Date());
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

  function resetClientImportDialog() {
    const form = $("#client-import-form");
    if (!form) return;
    form.reset();
    state.clientImport = { filename: "", clients: [], preview: null };
    $("#client-import-summary").hidden = true;
    $("#client-import-preview-body").innerHTML = "";
    $("#client-import-guidance").textContent = "";
    const previewButton = $("#client-import-preview-button");
    const confirmButton = $("#client-import-confirm-button");
    previewButton.disabled = false;
    previewButton.textContent = "Conferir arquivo";
    delete previewButton.dataset.originalLabel;
    confirmButton.hidden = true;
    confirmButton.disabled = true;
    confirmButton.textContent = "Importar clientes";
    delete confirmButton.dataset.originalLabel;
  }

  function clearClientImportPreview() {
    state.clientImport = { filename: "", clients: [], preview: null };
    $("#client-import-summary").hidden = true;
    $("#client-import-preview-body").innerHTML = "";
    $("#client-import-guidance").textContent = "";
    const confirmButton = $("#client-import-confirm-button");
    confirmButton.hidden = true;
    confirmButton.disabled = true;
  }

  function resetUserDialog() {
    const dialog = document.getElementById("user-dialog");
    const form = document.getElementById("user-form");
    if (!dialog || !form) return;
    form.reset();
    state.editingUserId = null;
    form.elements.email.readOnly = false;
    form.elements.email.required = true;
    form.elements.password.required = true;
    $("#user-email-field").hidden = false;
    $("#user-password-field").hidden = false;
    $("#user-password-help").hidden = false;
    $(".modal-header h2", dialog).textContent = "Novo membro";
    const submit = $('button[type="submit"]', form);
    submit.textContent = "Cadastrar membro";
    delete submit.dataset.originalLabel;
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

  function resetCrmDialog(dialogId) {
    const entry = Object.entries(crmDefinitions).find(([, definition]) => definition.dialogId === dialogId);
    if (!entry) return;
    const [kind, definition] = entry;
    const dialog = document.getElementById(definition.dialogId);
    const form = document.getElementById(definition.formId);
    if (!dialog || !form) return;
    form.reset();
    state.editingCrm[kind] = null;
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
      if (state.user.must_change_password) {
        setView("settings");
        window.setTimeout(() => $("#current-password").focus(), 50);
        toast("Antes de continuar, substitua a senha temporária.");
      } else {
        toast("Acesso realizado com sucesso.");
      }
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
      loadSettings(),
      checkHealth()
    ];
    if (state.currentView === "clientDetail" && state.selectedClient) {
      loaders.push(loadClientDetail(state.selectedClient.id));
    }
    if (state.currentView === "audit" && canViewAudit()) {
      loaders.push(loadAudit(state.audit.page));
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
    const [summary, contacts, opportunities, tasks, interactions] = await Promise.all([
      api("/api/v1/crm/summary"),
      api("/api/v1/crm/contacts?limit=100"),
      api("/api/v1/crm/opportunities?limit=100"),
      api("/api/v1/crm/tasks?limit=100"),
      api("/api/v1/crm/interactions?limit=100")
    ]);
    state.crm = {
      summary,
      contacts: Array.isArray(contacts) ? contacts : contacts.items || [],
      opportunities: Array.isArray(opportunities) ? opportunities : opportunities.items || [],
      tasks: Array.isArray(tasks) ? tasks : tasks.items || [],
      interactions: Array.isArray(interactions) ? interactions : interactions.items || []
    };
    renderCrm();
    renderDashboard();
  }

  async function loadUsers() {
    const response = await api("/api/v1/users?page=1&page_size=50");
    state.users = Array.isArray(response) ? response : response.items || [];
    renderUsers();
    fillAuditUserFilter();
  }

  function fillAuditUserFilter() {
    const select = $("#audit-user-filter");
    if (!select) return;
    const selected = state.audit.filters.userId || "all";
    select.innerHTML = '<option value="all">Todos</option>' + state.users.map((user) =>
      `<option value="${escapeHtml(user.id)}">${escapeHtml(user.full_name || user.email)}</option>`
    ).join("");
    select.value = Array.from(select.options).some((option) => option.value === selected) ? selected : "all";
  }

  async function loadAudit(page = 1) {
    if (!canViewAudit()) return;
    const filters = state.audit.filters;
    const params = new URLSearchParams({ page: String(page), page_size: String(state.audit.pageSize) });
    if (filters.search.trim()) params.set("q", filters.search.trim());
    if (filters.entityType !== "all") params.set("entity_type", filters.entityType);
    if (filters.action !== "all") params.set("action", filters.action);
    if (filters.userId !== "all") params.set("user_id", filters.userId);
    if (filters.dateFrom) params.set("date_from", filters.dateFrom);
    if (filters.dateTo) params.set("date_to", filters.dateTo);
    $("#audit-list").innerHTML = '<div class="loading-row">Carregando atividades…</div>';
    const response = await api(`/api/v1/audit?${params.toString()}`);
    state.audit.items = Array.isArray(response.items) ? response.items : [];
    state.audit.total = Number(response.total || 0);
    state.audit.page = Number(response.page || page);
    state.audit.pages = Number(response.pages || 0);
    renderAudit();
  }

  async function loadSettings() {
    const [organization, sessions] = await Promise.all([
      api("/api/v1/organizations/current"),
      api("/api/v1/sessions")
    ]);
    state.organization = organization;
    state.sessions = Array.isArray(sessions) ? sessions : [];
    renderSettings();
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
    const status = $("#client-status-filter").value;
    const clients = state.clients.filter((client) => {
      const matchesTerm = [client.full_name, client.cpf, client.city, client.email]
        .some((value) => String(value || "").toLocaleLowerCase("pt-BR").includes(term));
      const matchesStatus = status === "all" || String(client.status || "") === status;
      return matchesTerm && matchesStatus;
    });
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

  async function downloadClientsCsv() {
    if (!canExportClients()) {
      toast("Seu perfil não possui permissão para exportar clientes.", "error");
      return;
    }

    const button = $("#export-clients-button");
    const params = new URLSearchParams();
    const query = $("#client-search").value.trim();
    const status = $("#client-status-filter").value;
    if (query) params.set("q", query);
    if (status !== "all") params.set("status", status);

    setBusy(button, true, "Gerando…");
    try {
      const headers = new Headers();
      const access = getTokens().access;
      if (access) headers.set("Authorization", `Bearer ${access}`);
      const suffix = params.toString() ? `?${params.toString()}` : "";
      const response = await fetch(`${API_BASE}/api/v1/clients/export.csv${suffix}`, { headers });
      if (response.status === 401) {
        clearSession();
        showLogin("Sua sessão expirou. Entre novamente.");
        throw new Error("Sessão expirada.");
      }
      if (!response.ok) throw new Error(await readError(response));

      const blob = await response.blob();
      const today = new Date();
      const date = [
        today.getFullYear(),
        String(today.getMonth() + 1).padStart(2, "0"),
        String(today.getDate()).padStart(2, "0")
      ].join("-");
      const link = document.createElement("a");
      const objectUrl = URL.createObjectURL(blob);
      link.href = objectUrl;
      link.download = `clientes_${date}.csv`;
      link.hidden = true;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
      toast("Lista de clientes exportada em CSV.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function formatImportCpf(value) {
    const digits = String(value || "").replace(/\D/g, "");
    if (digits.length !== 11) return value || "—";
    return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`;
  }

  function renderClientImportPreview(preview) {
    $("#import-total-count").textContent = preview.total_rows || 0;
    $("#import-valid-count").textContent = preview.valid_rows || 0;
    $("#import-invalid-count").textContent = preview.invalid_rows || 0;
    $("#import-duplicate-count").textContent = preview.duplicate_rows || 0;
    $("#client-import-preview-body").innerHTML = preview.rows.map((row) => {
      const name = row.data?.full_name || row.display_name || "—";
      const cpf = row.data?.cpf || row.display_cpf || "—";
      const result = row.valid
        ? '<span class="import-result valid">✓ Pronto para importar</span>'
        : `<span class="import-result invalid">${escapeHtml((row.errors || []).join(" ") || "Registro inválido.")}</span>`;
      return `<tr class="${row.valid ? "" : "import-row-invalid"}">
        <td>${escapeHtml(row.line)}</td>
        <td><strong>${escapeHtml(name)}</strong></td>
        <td>${escapeHtml(formatImportCpf(cpf))}</td>
        <td>${result}</td>
      </tr>`;
    }).join("");

    const guidance = $("#client-import-guidance");
    if (preview.valid_rows && preview.invalid_rows) {
      guidance.textContent = `${preview.valid_rows} cliente(s) pronto(s). As ${preview.invalid_rows} linha(s) com problema não serão importadas.`;
    } else if (preview.valid_rows) {
      guidance.textContent = "Todos os clientes estão prontos. Confira a prévia e confirme a importação.";
    } else {
      guidance.textContent = "Nenhum cliente pode ser importado. Corrija o CSV e confira novamente.";
    }
    $("#client-import-summary").hidden = false;
    const confirmButton = $("#client-import-confirm-button");
    confirmButton.hidden = preview.valid_rows < 1;
    confirmButton.disabled = preview.valid_rows < 1;
    confirmButton.textContent = preview.valid_rows === 1
      ? "Importar 1 cliente"
      : `Importar ${preview.valid_rows} clientes`;
    delete confirmButton.dataset.originalLabel;
  }

  async function previewClientImport(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity() || !canImportClients()) return;
    const file = form.elements.file.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) {
      toast("Selecione um arquivo com extensão .csv.", "error");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      toast("O CSV deve ter no máximo 2 MB.", "error");
      return;
    }

    const button = $("#client-import-preview-button");
    const body = new FormData();
    body.append("file", file, file.name);
    setBusy(button, true, "Conferindo…");
    clearClientImportPreview();
    try {
      const preview = await api("/api/v1/clients/import/preview", { method: "POST", body });
      state.clientImport = {
        filename: preview.filename || file.name,
        clients: preview.rows.filter((row) => row.valid && row.data).map((row) => row.data),
        preview
      };
      renderClientImportPreview(preview);
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function confirmClientImport() {
    if (!canImportClients() || !state.clientImport.clients.length) return;
    const button = $("#client-import-confirm-button");
    const count = state.clientImport.clients.length;
    setBusy(button, true, "Importando…");
    try {
      const result = await api("/api/v1/clients/import", {
        method: "POST",
        body: JSON.stringify({
          source_filename: state.clientImport.filename,
          clients: state.clientImport.clients
        })
      });
      closeDialog($("#client-import-dialog"));
      const refreshed = await Promise.allSettled([loadClients(), loadDashboard()]);
      const message = result.imported === 1
        ? "1 cliente importado com sucesso."
        : `${result.imported} clientes importados com sucesso.`;
      toast(refreshed.some((request) => request.status === "rejected")
        ? `${message} Clique em Atualizar para recarregar a tela.`
        : message);
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function fillClientSelects() {
    const options = state.clients.map((client) => `<option value="${escapeHtml(client.id)}">${escapeHtml(client.full_name)}</option>`).join("");
    $("#opportunity-client").innerHTML = `<option value="">Selecione</option>${options}`;
    $("#task-client").innerHTML = `<option value="">Sem cliente vinculado</option>${options}`;
    $("#interaction-client").innerHTML = `<option value="">Selecione</option>${options}`;
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

  function toLocalDateTimeValue(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    const pad = (part) => String(part).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
  }

  async function openCrmEditor(kind, itemId) {
    const definition = crmDefinitions[kind];
    const item = definition && state.crm[definition.collection].find((record) => String(record.id) === String(itemId));
    if (!definition || !item) {
      toast("Registro do CRM não encontrado.", "error");
      return;
    }

    if (["opportunity", "task"].includes(kind)) {
      try {
        await loadClients();
      } catch (error) {
        toast(error.message || "Não foi possível carregar os clientes.", "error");
        return;
      }
    }

    resetCrmDialog(definition.dialogId);
    state.editingCrm[kind] = item.id;
    const dialog = document.getElementById(definition.dialogId);
    const form = document.getElementById(definition.formId);

    if (kind === "contact") {
      form.elements.name.value = item.name || "";
      form.elements.position.value = item.position || "";
      form.elements.email.value = item.email || "";
      form.elements.phone.value = item.phone || "";
      form.elements.notes.value = item.notes || "";
    } else if (kind === "opportunity") {
      form.elements.title.value = item.title || "";
      setSelectValue(form.elements.client_id, item.client_id, clientName(item.client_id));
      setSelectValue(form.elements.stage, item.stage || "lead", stageLabels[item.stage]);
      form.elements.estimated_value.value = item.estimated_value ?? 0;
      form.elements.probability.value = item.probability ?? 0;
      form.elements.expected_close_date.value = item.expected_close_date || "";
      form.elements.notes.value = item.notes || "";
    } else if (kind === "task") {
      form.elements.title.value = item.title || "";
      setSelectValue(form.elements.client_id, item.client_id, clientName(item.client_id));
      setSelectValue(form.elements.priority, item.priority || "normal", priorityLabels[item.priority]);
      setSelectValue(form.elements.status, item.status || "pending", taskStatusLabels[item.status]);
      form.elements.due_at.value = toLocalDateTimeValue(item.due_at);
      form.elements.description.value = item.description || "";
    }

    $(".modal-header h2", dialog).textContent = definition.editTitle;
    const submit = $('button[type="submit"]', form);
    submit.textContent = "Salvar alterações";
    delete submit.dataset.originalLabel;
    dialog.showModal();
  }

  async function refreshCrm(message) {
    await Promise.all([loadCrm(), loadDashboard()]);
    if (message) toast(message);
  }

  async function deleteCrmItem(kind, itemId, button) {
    const definition = crmDefinitions[kind];
    if (!definition || !itemId) return;
    const warning = kind === "opportunity"
      ? " As tarefas vinculadas a ela também serão apagadas."
      : "";
    const article = ["opportunity", "task"].includes(kind) ? "esta" : "este";
    if (!window.confirm(`Deseja realmente apagar ${article} ${definition.singular}?${warning} Esta ação não pode ser desfeita.`)) return;

    setBusy(button, true, "Apagando…");
    try {
      await api(`/api/v1/crm/${definition.collection}/${itemId}`, { method: "DELETE" });
      const deletedMessage = {
        contact: "Contato apagado.",
        opportunity: "Oportunidade apagada.",
        task: "Tarefa apagada.",
        interaction: "Atendimento apagado."
      }[kind] || "Registro apagado.";
      await refreshCrm(deletedMessage);
    } catch (error) {
      toast(error.message, "error");
      setBusy(button, false);
    }
  }

  async function completeCrmTask(itemId, button) {
    if (!itemId) return;
    setBusy(button, true, "Concluindo…");
    try {
      await api(`/api/v1/crm/tasks/${itemId}/complete`, { method: "POST" });
      await refreshCrm("Tarefa concluída.");
    } catch (error) {
      toast(error.message, "error");
      setBusy(button, false);
    }
  }

  async function changeOpportunityStage(itemId, stage, select) {
    if (!itemId || !stage) return;
    select.disabled = true;
    try {
      await api(`/api/v1/crm/opportunities/${itemId}`, { method: "PATCH", body: JSON.stringify({ stage }) });
      await refreshCrm(`Oportunidade movida para ${stageLabels[stage] || stage}.`);
    } catch (error) {
      toast(error.message, "error");
      select.disabled = false;
      renderCrm();
    }
  }

  function taskRow(task, showActions = false) {
    const priority = String(task.priority || "normal").toLowerCase();
    const taskStatus = String(task.status || "pending").toLowerCase();
    const isOverdue = task.due_at && new Date(task.due_at) < new Date() && !["completed", "cancelled"].includes(taskStatus);
    return `<div class="list-row crm-task-row ${taskStatus === "completed" ? "completed" : ""}">
      <span class="list-icon">${priority === "urgent" ? "!" : "✓"}</span>
      <span><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(task.client_id ? clientName(task.client_id) : priorityLabels[priority] || priority)} · ${escapeHtml(taskStatusLabels[taskStatus] || taskStatus)}</small></span>
      <span class="list-meta ${isOverdue ? "danger-text" : ""}">${escapeHtml(task.due_at ? formatDate(task.due_at, true) : "Sem prazo")}</span>
      ${showActions ? `<span class="crm-item-actions">
        ${!["completed", "cancelled"].includes(taskStatus) ? `<button class="complete-button" type="button" data-complete-task="${escapeHtml(task.id)}">Concluir</button>` : ""}
        <button class="edit-button" type="button" data-edit-task="${escapeHtml(task.id)}">Editar</button>
        <button class="delete-button" type="button" data-delete-task="${escapeHtml(task.id)}">Apagar</button>
      </span>` : ""}
    </div>`;
  }

  function renderCrm() {
    const summary = state.crm.summary || {};
    const filteredOpportunities = state.crm.opportunities.filter((item) => matchesCrmSearch(
      item.title,
      clientName(item.client_id),
      stageLabels[item.stage],
      item.estimated_value,
      item.notes
    ));
    const filteredTasks = state.crm.tasks.filter((item) => {
      const status = String(item.status || "pending").toLowerCase();
      const priority = String(item.priority || "normal").toLowerCase();
      return matchesCrmSearch(item.title, item.description, clientName(item.client_id), taskStatusLabels[status], priorityLabels[priority])
        && (state.crmFilters.taskStatus === "all" || status === state.crmFilters.taskStatus)
        && (state.crmFilters.priority === "all" || priority === state.crmFilters.priority);
    });
    const filteredContacts = state.crm.contacts.filter((item) => matchesCrmSearch(
      item.name,
      item.position,
      item.email,
      item.phone,
      item.notes,
      clientName(item.client_id)
    ));
    const filteredInteractions = state.crm.interactions.filter((item) => {
      const interactionType = String(item.interaction_type || "other").toLowerCase();
      return matchesCrmSearch(item.subject, item.description, clientName(item.client_id), interactionTypeLabels[interactionType])
        && (state.crmFilters.interactionType === "all" || interactionType === state.crmFilters.interactionType);
    });
    const totalRecords = state.crm.opportunities.length + state.crm.tasks.length + state.crm.contacts.length + state.crm.interactions.length;
    const shownRecords = filteredOpportunities.length + filteredTasks.length + filteredContacts.length + filteredInteractions.length;

    $("#crm-contacts-count").textContent = summary.contacts ?? state.crm.contacts.length;
    $("#crm-opportunities-count").textContent = summary.opportunities ?? state.crm.opportunities.length;
    $("#crm-open-value").textContent = formatCurrency(summary.open_pipeline_value);
    $("#crm-pending-count").textContent = summary.pending_tasks ?? 0;
    $("#crm-filter-summary").textContent = `Mostrando ${shownRecords} de ${totalRecords} ${totalRecords === 1 ? "registro" : "registros"}`;

    const boardStages = ["lead", "qualified", "proposal", "negotiation", "won", "lost"];
    $("#opportunity-board").innerHTML = boardStages.map((stage) => {
      const opportunities = filteredOpportunities.filter((item) => item.stage === stage);
      return `<section class="stage-column">
        <div class="stage-header"><strong>${stageLabels[stage]}</strong><span>${opportunities.length}</span></div>
        ${opportunities.length ? opportunities.map((item) => `<article class="opportunity-card">
          <h4>${escapeHtml(item.title)}</h4>
          <p>${escapeHtml(clientName(item.client_id))}</p>
          <p><strong>${formatCurrency(item.estimated_value)}</strong> · ${Number(item.probability || 0)}%</p>
          <p>Previsão: ${formatDate(item.expected_close_date)}</p>
          <label class="stage-control"><span>Etapa</span><select data-opportunity-stage="${escapeHtml(item.id)}" aria-label="Alterar etapa de ${escapeHtml(item.title)}">
            ${Object.entries(stageLabels).map(([value, label]) => `<option value="${value}" ${value === item.stage ? "selected" : ""}>${escapeHtml(label)}</option>`).join("")}
          </select></label>
          <div class="crm-item-actions">
            <button class="edit-button" type="button" data-edit-opportunity="${escapeHtml(item.id)}">Editar</button>
            <button class="delete-button" type="button" data-delete-opportunity="${escapeHtml(item.id)}">Apagar</button>
          </div>
        </article>`).join("") : '<div class="empty-state">Sem oportunidades</div>'}
      </section>`;
    }).join("");

    $("#task-list").innerHTML = filteredTasks.length ? filteredTasks.map((task) => taskRow(task, true)).join("") : '<div class="empty-state">Nenhuma tarefa encontrada com os filtros atuais.</div>';
    $("#contact-count").textContent = `${filteredContacts.length} de ${state.crm.contacts.length} ${state.crm.contacts.length === 1 ? "contato" : "contatos"}`;
    $("#contact-list").innerHTML = filteredContacts.length ? filteredContacts.map((contact) => `<article class="contact-card">
      <span class="avatar">${escapeHtml(initials(contact.name))}</span>
      <h4>${escapeHtml(contact.name)}</h4>
      <p>${escapeHtml(contact.position || "Contato comercial")}</p>
      <p>${escapeHtml(contact.email || "E-mail não informado")}</p>
      <p>${escapeHtml(contact.phone || "")}</p>
      <div class="crm-item-actions">
        <button class="edit-button" type="button" data-edit-contact="${escapeHtml(contact.id)}">Editar</button>
        <button class="delete-button" type="button" data-delete-contact="${escapeHtml(contact.id)}">Apagar</button>
      </div>
    </article>`).join("") : '<div class="empty-state">Nenhum contato encontrado com os filtros atuais.</div>';

    $("#interaction-count").textContent = `${filteredInteractions.length} de ${state.crm.interactions.length} ${state.crm.interactions.length === 1 ? "atendimento" : "atendimentos"}`;
    $("#interaction-list").innerHTML = filteredInteractions.length ? filteredInteractions.map((interaction) => {
      const interactionType = String(interaction.interaction_type || "other").toLowerCase();
      return `<article class="interaction-item">
        <span class="interaction-marker" aria-hidden="true"></span>
        <div class="interaction-content">
          <div class="interaction-heading"><span class="badge neutral">${escapeHtml(interactionTypeLabels[interactionType] || interactionType)}</span><time>${escapeHtml(formatDate(interaction.occurred_at, true))}</time></div>
          <h4>${escapeHtml(interaction.subject)}</h4>
          <p class="interaction-client">${escapeHtml(clientName(interaction.client_id))}</p>
          ${interaction.description ? `<p>${escapeHtml(interaction.description)}</p>` : ""}
        </div>
        <button class="delete-button" type="button" data-delete-interaction="${escapeHtml(interaction.id)}">Apagar</button>
      </article>`;
    }).join("") : '<div class="empty-state">Nenhum atendimento encontrado com os filtros atuais.</div>';
  }

  function renderUsers() {
    const administrator = canManageUsers();
    $("#new-user-button").hidden = !administrator;
    $("#user-count").textContent = `${state.users.length} ${state.users.length === 1 ? "membro" : "membros"}`;
    $("#user-list").innerHTML = state.users.length ? state.users.map((user) => {
      const currentAccount = String(user.id) === String(state.user?.id);
      const active = String(user.status || "active") === "active";
      return `<article class="person-row">
        <span class="avatar">${escapeHtml(initials(user.full_name))}</span>
        <div><h4>${escapeHtml(user.full_name)}</h4><p>${escapeHtml(user.email)}</p>${user.must_change_password ? '<small class="password-pending">Troca de senha pendente</small>' : ""}</div>
        <span>${escapeHtml(userRoleLabels[user.role] || user.role || "Equipe")}</span>
        <span class="badge ${active ? "" : "neutral"}">${escapeHtml(userStatusLabels[user.status] || user.status || "Ativo")}</span>
        <span class="team-actions">${currentAccount
          ? '<span class="current-account">Conta atual</span>'
          : administrator
            ? `<button class="edit-button" type="button" data-edit-user="${escapeHtml(user.id)}">Editar</button><button class="${active ? "delete-button" : "complete-button"}" type="button" data-toggle-user="${escapeHtml(user.id)}" data-user-action="${active ? "block" : "unblock"}">${active ? "Desativar" : "Ativar"}</button>`
            : ""}</span>
      </article>`;
    }).join("") : '<div class="empty-state">Nenhum usuário encontrado.</div>';
  }

  function auditDetailValue(key, value) {
    if (value === null || value === undefined || value === "") return "—";
    if (["amount", "estimated_value", "current_balance", "monthly_installment"].includes(key)) {
      return formatCurrency(value);
    }
    if (typeof value === "boolean") return value ? "Sim" : "Não";
    if (key === "stage") return stageLabels[value] || value;
    if (key === "priority") return priorityLabels[value] || value;
    if (key === "nature") return debtNatureLabels[value] || value;
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  }

  function renderAudit() {
    const total = state.audit.total;
    const pages = Math.max(state.audit.pages, 1);
    $("#audit-count").textContent = `${total} ${total === 1 ? "atividade" : "atividades"}`;
    $("#audit-page-label").textContent = `Página ${state.audit.page} de ${pages}`;
    $("#audit-previous-page").disabled = state.audit.page <= 1;
    $("#audit-next-page").disabled = state.audit.page >= pages || total === 0;
    $("#audit-list").innerHTML = state.audit.items.length ? state.audit.items.map((event) => {
      const entity = auditEntityLabels[event.entity_type] || event.entity_type || "Registro";
      const action = auditActionLabels[event.action] || event.action || "Realizou uma ação";
      const details = Object.entries(event.details || {}).slice(0, 8).map(([key, value]) =>
        `<span><strong>${escapeHtml(auditDetailLabels[key] || key)}:</strong> ${escapeHtml(auditDetailValue(key, value))}</span>`
      ).join("");
      return `<article class="audit-item">
        <span class="audit-marker" aria-hidden="true"></span>
        <div class="audit-content">
          <div class="audit-item-heading"><div><strong>${escapeHtml(event.actor_name || "Sistema")}</strong>${event.actor_email ? `<small>${escapeHtml(event.actor_email)}</small>` : ""}</div><time>${escapeHtml(formatDate(event.occurred_at, true))}</time></div>
          <p><span class="audit-action-badge action-${escapeHtml(event.action || "other")}">${escapeHtml(action)}</span><span class="audit-entity-label">${escapeHtml(entity)}</span></p>
          ${details ? `<div class="audit-details">${details}</div>` : ""}
        </div>
      </article>`;
    }).join("") : '<div class="empty-state">Nenhuma atividade encontrada com os filtros atuais.</div>';
  }

  function renderSettings() {
    const organization = state.organization || state.user?.organization || {};
    const organizationForm = $("#organization-form");
    organizationForm.elements.legal_name.value = organization.legal_name || "";
    organizationForm.elements.trade_name.value = organization.trade_name || "";
    organizationForm.elements.email.value = organization.email || "";
    organizationForm.elements.phone.value = organization.phone || "";

    const editable = canUpdateOrganization();
    Array.from(organizationForm.elements).forEach((element) => {
      element.disabled = !editable;
    });
    $("#save-organization-button").hidden = !editable;
    $("#organization-permission-note").textContent = editable
      ? "As alterações são aplicadas à organização atual."
      : "Seu perfil pode consultar, mas não alterar estes dados.";

    const activeSessions = state.sessions.filter(sessionIsActive);
    $("#session-count").textContent = `${activeSessions.length} ${activeSessions.length === 1 ? "sessão ativa" : "sessões ativas"}`;
    $("#revoke-all-sessions").hidden = !activeSessions.length;
    $("#session-list").innerHTML = activeSessions.length ? activeSessions.map((session) => `<article class="session-row">
      <span class="session-icon" aria-hidden="true">✓</span>
      <div><h4>${escapeHtml(sessionDevice(session.user_agent))}</h4><p>Iniciada em ${escapeHtml(formatDate(session.created_at, true))}</p><small>${escapeHtml(session.ip_address ? `IP ${session.ip_address}` : "IP não informado")} · expira em ${escapeHtml(formatDate(session.expires_at, true))}</small></div>
      <button class="delete-button" type="button" data-revoke-session="${escapeHtml(session.id)}">Encerrar</button>
    </article>`).join("") : '<div class="empty-state">Nenhuma sessão ativa encontrada.</div>';
  }

  async function submitOrganization(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity() || !canUpdateOrganization() || !state.organization?.id) return;
    const button = $("#save-organization-button");
    const values = Object.fromEntries(new FormData(form));
    const payload = {
      legal_name: String(values.legal_name || "").trim(),
      trade_name: String(values.trade_name || "").trim() || null,
      email: String(values.email || "").trim() || null,
      phone: String(values.phone || "").trim() || null
    };
    setBusy(button, true, "Salvando…");
    try {
      state.organization = await api(`/api/v1/organizations/${state.organization.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload)
      });
      state.user.organization = {
        id: state.organization.id,
        legal_name: state.organization.legal_name,
        trade_name: state.organization.trade_name,
        status: state.organization.status
      };
      renderSettings();
      toast("Dados da organização atualizados.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function submitPasswordChange(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const currentPassword = form.elements.current_password.value;
    const newPassword = form.elements.new_password.value;
    const confirmation = form.elements.password_confirmation.value;
    if (newPassword !== confirmation) {
      toast("A confirmação da nova senha não confere.", "error");
      form.elements.password_confirmation.focus();
      return;
    }
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Alterando…");
    try {
      await api("/api/v1/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
      });
      form.reset();
      clearSession();
      showLogin("Senha alterada. Todas as sessões foram encerradas; entre novamente com a nova senha.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function revokeSession(sessionId, button) {
    if (!window.confirm("Deseja encerrar esta sessão? O token de renovação será revogado.")) return;
    setBusy(button, true, "Encerrando…");
    try {
      await api(`/api/v1/sessions/${sessionId}`, { method: "DELETE" });
      await loadSettings();
      toast("Sessão encerrada com segurança.");
    } catch (error) {
      toast(error.message, "error");
      setBusy(button, false);
    }
  }

  async function revokeAllSessions(button) {
    if (!window.confirm("Deseja encerrar todas as sessões, inclusive esta? Será necessário entrar novamente.")) return;
    setBusy(button, true, "Encerrando…");
    try {
      await api("/api/v1/sessions", { method: "DELETE" });
      clearSession();
      showLogin("Todas as sessões foram encerradas com segurança.");
    } catch (error) {
      toast(error.message, "error");
      setBusy(button, false);
    }
  }

  function openUserEditor(userId) {
    if (!canManageUsers()) {
      toast("Somente administradores podem alterar a equipe.", "error");
      return;
    }
    const user = state.users.find((item) => String(item.id) === String(userId));
    if (!user || String(user.id) === String(state.user?.id)) {
      toast("A conta atualmente conectada não pode ser alterada nesta tela.", "error");
      return;
    }
    resetUserDialog();
    state.editingUserId = user.id;
    const dialog = document.getElementById("user-dialog");
    const form = document.getElementById("user-form");
    form.elements.full_name.value = user.full_name || "";
    setSelectValue(form.elements.role, user.role || "atendimento", userRoleLabels[user.role]);
    form.elements.password.required = false;
    form.elements.email.required = false;
    $("#user-email-field").hidden = true;
    $("#user-password-field").hidden = true;
    $("#user-password-help").hidden = true;
    $(".modal-header h2", dialog).textContent = "Editar membro";
    const submit = $('button[type="submit"]', form);
    submit.textContent = "Salvar alterações";
    delete submit.dataset.originalLabel;
    dialog.showModal();
  }

  async function submitUser(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity() || !canManageUsers()) return;
    const button = $('button[type="submit"]', form);
    const editingId = state.editingUserId;
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      const payload = editingId
        ? { full_name: data.full_name, role: data.role }
        : { full_name: data.full_name, email: data.email, password: data.password, role: data.role || "atendimento" };
      const path = editingId ? `/api/v1/users/${editingId}` : "/api/v1/users";
      await api(path, { method: editingId ? "PATCH" : "POST", body: JSON.stringify(payload) });
      closeDialog(form.closest("dialog"));
      await loadUsers();
      toast(editingId ? "Membro atualizado." : "Membro cadastrado. A senha deverá ser trocada no primeiro acesso.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function toggleUserStatus(userId, action, button) {
    if (!canManageUsers()) {
      toast("Somente administradores podem alterar a equipe.", "error");
      return;
    }
    const user = state.users.find((item) => String(item.id) === String(userId));
    if (!user || String(user.id) === String(state.user?.id)) {
      toast("Não é possível desativar a conta atualmente conectada.", "error");
      return;
    }
    if (action === "block" && !window.confirm(`Deseja desativar o acesso de ${user.full_name}? As sessões abertas serão encerradas.`)) return;
    setBusy(button, true, action === "block" ? "Desativando…" : "Ativando…");
    try {
      await api(`/api/v1/users/${user.id}/${action}`, { method: "POST" });
      await loadUsers();
      toast(action === "block" ? "Acesso desativado." : "Acesso reativado.");
    } catch (error) {
      toast(error.message, "error");
      setBusy(button, false);
    }
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
    const editingId = state.editingCrm.contact;
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      const payload = {
        name: data.name,
        position: data.position || null,
        email: data.email || null,
        phone: data.phone || null,
        notes: data.notes || null
      };
      const path = editingId ? `/api/v1/crm/contacts/${editingId}` : "/api/v1/crm/contacts";
      await api(path, { method: editingId ? "PATCH" : "POST", body: JSON.stringify(payload) });
      closeDialog(form.closest("dialog"));
      await refreshCrm(editingId ? "Contato atualizado." : "Contato cadastrado.");
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
    const editingId = state.editingCrm.opportunity;
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      const payload = {
        title: data.title,
        client_id: data.client_id,
        stage: data.stage || "lead",
        estimated_value: Number(data.estimated_value || 0),
        probability: Number(data.probability || 0),
        expected_close_date: data.expected_close_date || null,
        notes: data.notes || null
      };
      const path = editingId ? `/api/v1/crm/opportunities/${editingId}` : "/api/v1/crm/opportunities";
      await api(path, { method: editingId ? "PATCH" : "POST", body: JSON.stringify(payload) });
      closeDialog(form.closest("dialog"));
      await refreshCrm(editingId ? "Oportunidade atualizada." : "Oportunidade cadastrada.");
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
    const editingId = state.editingCrm.task;
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      const payload = {
        title: data.title,
        client_id: data.client_id || null,
        priority: data.priority || "normal",
        status: data.status || "pending",
        due_at: data.due_at ? new Date(data.due_at).toISOString() : null,
        description: data.description || null
      };
      const path = editingId ? `/api/v1/crm/tasks/${editingId}` : "/api/v1/crm/tasks";
      await api(path, { method: editingId ? "PATCH" : "POST", body: JSON.stringify(payload) });
      closeDialog(form.closest("dialog"));
      await refreshCrm(editingId ? "Tarefa atualizada." : "Tarefa cadastrada.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function submitInteraction(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      const payload = {
        client_id: data.client_id,
        interaction_type: data.interaction_type || "note",
        subject: data.subject,
        occurred_at: new Date(data.occurred_at).toISOString(),
        description: data.description || null
      };
      await api("/api/v1/crm/interactions", { method: "POST", body: JSON.stringify(payload) });
      closeDialog(form.closest("dialog"));
      await refreshCrm("Atendimento registrado.");
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
      audit: async () => {
        await loadAudit(state.audit.page);
        toast("Histórico atualizado.");
      },
      settings: async () => {
        await Promise.all([checkHealth(), loadSettings()]);
        toast("Configurações atualizadas.");
      }
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
    $("#client-status-filter").addEventListener("change", renderClients);
    $("#export-clients-button").addEventListener("click", downloadClientsCsv);
    $("#client-import-form").addEventListener("submit", previewClientImport);
    $("#client-import-confirm-button").addEventListener("click", confirmClientImport);
    $("#client-import-file").addEventListener("change", clearClientImportPreview);
    $("#crm-search").addEventListener("input", (event) => {
      state.crmFilters.search = event.currentTarget.value;
      renderCrm();
    });
    $("#crm-task-status-filter").addEventListener("change", (event) => {
      state.crmFilters.taskStatus = event.currentTarget.value;
      renderCrm();
    });
    $("#crm-priority-filter").addEventListener("change", (event) => {
      state.crmFilters.priority = event.currentTarget.value;
      renderCrm();
    });
    $("#crm-interaction-type-filter").addEventListener("change", (event) => {
      state.crmFilters.interactionType = event.currentTarget.value;
      renderCrm();
    });
    $("#clear-crm-filters").addEventListener("click", () => {
      state.crmFilters = { search: "", taskStatus: "all", priority: "all", interactionType: "all" };
      $("#crm-search").value = "";
      $("#crm-task-status-filter").value = "all";
      $("#crm-priority-filter").value = "all";
      $("#crm-interaction-type-filter").value = "all";
      renderCrm();
    });
    $("#audit-filter-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.currentTarget));
      if (values.date_from && values.date_to && values.date_from > values.date_to) {
        toast("A data inicial não pode ser posterior à data final.", "error");
        return;
      }
      state.audit.filters = {
        search: String(values.search || ""),
        entityType: String(values.entity_type || "all"),
        action: String(values.action || "all"),
        userId: String(values.user_id || "all"),
        dateFrom: String(values.date_from || ""),
        dateTo: String(values.date_to || "")
      };
      try {
        await loadAudit(1);
      } catch (error) {
        toast(error.message, "error");
      }
    });
    $("#clear-audit-filters").addEventListener("click", async () => {
      $("#audit-filter-form").reset();
      state.audit.filters = { search: "", entityType: "all", action: "all", userId: "all", dateFrom: "", dateTo: "" };
      try {
        await loadAudit(1);
      } catch (error) {
        toast(error.message, "error");
      }
    });
    $("#audit-previous-page").addEventListener("click", () => {
      if (state.audit.page > 1) loadAudit(state.audit.page - 1).catch((error) => toast(error.message, "error"));
    });
    $("#audit-next-page").addEventListener("click", () => {
      if (state.audit.page < state.audit.pages) loadAudit(state.audit.page + 1).catch((error) => toast(error.message, "error"));
    });
    $("#client-form").addEventListener("submit", submitClient);
    $("#user-form").addEventListener("submit", submitUser);
    $("#organization-form").addEventListener("submit", submitOrganization);
    $("#password-form").addEventListener("submit", submitPasswordChange);
    $("#contact-form").addEventListener("submit", submitContact);
    $("#opportunity-form").addEventListener("submit", submitOpportunity);
    $("#task-form").addEventListener("submit", submitTask);
    $("#interaction-form").addEventListener("submit", submitInteraction);
    $("#income-form").addEventListener("submit", submitIncome);
    $("#expense-form").addEventListener("submit", submitExpense);
    $("#debt-form").addEventListener("submit", submitDebt);
    $("#clients-table").addEventListener("click", (event) => {
      const button = event.target.closest("[data-client-detail]");
      if (button) openClientDetail(button.dataset.clientDetail);
    });
    $("#new-user-button").addEventListener("click", () => openDialog("user-dialog"));
    $("#user-list").addEventListener("click", (event) => {
      const editButton = event.target.closest("[data-edit-user]");
      const toggleButton = event.target.closest("[data-toggle-user]");
      if (editButton) openUserEditor(editButton.dataset.editUser);
      else if (toggleButton) toggleUserStatus(toggleButton.dataset.toggleUser, toggleButton.dataset.userAction, toggleButton);
    });
    $("#session-list").addEventListener("click", (event) => {
      const button = event.target.closest("[data-revoke-session]");
      if (button) revokeSession(button.dataset.revokeSession, button);
    });
    $("#revoke-all-sessions").addEventListener("click", (event) => revokeAllSessions(event.currentTarget));
    $("#view-crm").addEventListener("click", (event) => {
      const editContact = event.target.closest("[data-edit-contact]");
      const editOpportunity = event.target.closest("[data-edit-opportunity]");
      const editTask = event.target.closest("[data-edit-task]");
      const deleteContact = event.target.closest("[data-delete-contact]");
      const deleteOpportunity = event.target.closest("[data-delete-opportunity]");
      const deleteTask = event.target.closest("[data-delete-task]");
      const deleteInteraction = event.target.closest("[data-delete-interaction]");
      const completeTask = event.target.closest("[data-complete-task]");
      if (editContact) openCrmEditor("contact", editContact.dataset.editContact);
      else if (editOpportunity) openCrmEditor("opportunity", editOpportunity.dataset.editOpportunity);
      else if (editTask) openCrmEditor("task", editTask.dataset.editTask);
      else if (deleteContact) deleteCrmItem("contact", deleteContact.dataset.deleteContact, deleteContact);
      else if (deleteOpportunity) deleteCrmItem("opportunity", deleteOpportunity.dataset.deleteOpportunity, deleteOpportunity);
      else if (deleteTask) deleteCrmItem("task", deleteTask.dataset.deleteTask, deleteTask);
      else if (deleteInteraction) deleteCrmItem("interaction", deleteInteraction.dataset.deleteInteraction, deleteInteraction);
      else if (completeTask) completeCrmTask(completeTask.dataset.completeTask, completeTask);
    });
    $("#view-crm").addEventListener("change", (event) => {
      const select = event.target.closest("[data-opportunity-stage]");
      if (select) changeOpportunityStage(select.dataset.opportunityStage, select.value, select);
    });
    $("#toggle-password").addEventListener("click", () => {
      const input = $("#login-password");
      const visible = input.type === "text";
      input.type = visible ? "password" : "text";
      $("#toggle-password").textContent = visible ? "Mostrar" : "Ocultar";
    });
    $$("[data-view]").forEach((button) => button.addEventListener("click", () => {
      setView(button.dataset.view);
      if (button.dataset.view === "settings") loadSettings().catch((error) => toast(error.message, "error"));
      if (button.dataset.view === "audit" && canViewAudit()) loadAudit(1).catch((error) => toast(error.message, "error"));
    }));
    $$("[data-view-link]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.viewLink)));
    $$("[data-open-dialog]").forEach((button) => button.addEventListener("click", () => openDialog(button.dataset.openDialog)));
    $$("[data-close-dialog]").forEach((button) => button.addEventListener("click", () => closeDialog(button.closest("dialog"))));
    $("#client-dialog").addEventListener("close", resetClientDialog);
    $("#client-import-dialog").addEventListener("close", resetClientImportDialog);
    $("#user-dialog").addEventListener("close", resetUserDialog);
    Object.values(financialDefinitions).forEach((definition) => {
      document.getElementById(definition.dialogId)?.addEventListener("close", () => resetFinancialDialog(definition.dialogId));
    });
    Object.values(crmDefinitions).forEach((definition) => {
      document.getElementById(definition.dialogId)?.addEventListener("close", () => resetCrmDialog(definition.dialogId));
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
      if (state.user.must_change_password) {
        setView("settings");
        window.setTimeout(() => $("#current-password").focus(), 50);
      }
    } catch {
      showLogin("Entre novamente para continuar.");
    }
  }

  boot();
})();
