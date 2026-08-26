(function () {
  "use strict";

  const API_BASE = String(window.CS_CONFIG?.API_BASE_URL || "").replace(/\/$/, "");
  const state = {
    user: null,
    dashboard: null,
    alerts: { total: 0, criticalCount: 0, items: [], open: false },
    management: { report: null, filters: { period: "30", dateFrom: "", dateTo: "" } },
    agenda: { summary: null, workload: [], items: [], viewMode: "timeline", weekStart: null, filters: { search: "", kind: "all", status: "all", responsible: "all", dateFrom: "", dateTo: "" } },
    collections: { summary: null, workload: [], aging: [], items: [], total: 0, report: null, reportFilters: { dateFrom: "", dateTo: "" }, filters: { q: "", status: "all", dueFrom: "", dueTo: "", followUp: "all", promise: "all", responsible: "all", priority: "all", aging: "all", attention: "all", sortOrder: "recommended" }, selectedItem: null, selectedAssignmentItem: null, selectedIds: [], selectedActionId: null, actions: [] },
    clients: [],
    clientPage: { items: [], total: 0, page: 1, pageSize: 25, pages: 0, requestId: 0 },
    crm: { summary: null, contacts: [], opportunities: [], tasks: [], interactions: [] },
    crmFilters: { search: "", taskStatus: "all", priority: "all", interactionType: "all" },
    editingCrm: { contact: null, opportunity: null, task: null, interaction: null },
    selectedClient: null,
    editingClientId: null,
    clientImport: { filename: "", clients: [], preview: null },
    financial: { incomes: [], expenses: [], debts: [], creditors: [], agreements: [], diagnosis: null, history: [] },
    editingFinancial: null,
    installmentPaymentTarget: null,
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
    management: ["INTELIGÊNCIA OPERACIONAL", "Central Gerencial", "Atualizar"],
    clients: ["RELACIONAMENTO", "Clientes", "Novo cliente"],
    collections: ["AGENDA FINANCEIRA", "Cobranças", "Atualizar"],
    agenda: ["ROTINA UNIFICADA", "Agenda operacional", "Atualizar"],
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
  const attentionLabels = { routine: "Rotina", attention: "Exige atenção", critical: "Crítica" };

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
    payment_agreement: "Acordo de pagamento",
    payment_installment: "Parcela e pagamento",
    collection_action: "Ação de cobrança",
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
    cancel: "Anulou",
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
    negotiated_amount: "Valor negociado",
    payment_method: "Forma de pagamento",
    nature: "Natureza",
    legal_name: "Razão social",
    trade_name: "Nome de apresentação",
    version: "Versão",
    eligibility_score: "Pontuação",
    eligibility_result: "Resultado",
    count: "Quantidade",
    query: "Pesquisa",
    source_filename: "Arquivo",
    installment_number: "Parcela"
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

  const paymentMethodLabels = {
    pix: "Pix",
    bank_slip: "Boleto",
    bank_transfer: "Transferência bancária",
    cash: "Dinheiro",
    credit_card: "Cartão de crédito",
    debit_card: "Cartão de débito",
    automatic_debit: "Débito automático",
    other: "Outra forma"
  };

  const agreementStatusLabels = {
    draft: "Rascunho",
    active: "Em andamento",
    completed: "Concluído",
    defaulted: "Inadimplente",
    cancelled: "Cancelado"
  };

  const installmentStatusLabels = {
    pending: "Pendente",
    paid: "Paga",
    overdue: "Atrasada",
    cancelled: "Cancelada"
  };

  const collectionStatusLabels = {
    pending: "Pendente",
    due_soon: "Vence em breve",
    paid: "Paga",
    overdue: "Atrasada",
    cancelled: "Cancelada"
  };

  const collectionActionTypeLabels = {
    phone: "Ligação",
    whatsapp: "WhatsApp",
    email: "E-mail",
    negotiation: "Negociação",
    other: "Outro canal"
  };

  const collectionOutcomeLabels = {
    contacted: "Cliente contatado",
    no_answer: "Sem resposta",
    promise_to_pay: "Promessa de pagamento",
    refused: "Recusou o pagamento",
    other: "Outro resultado"
  };

  const financialDefinitions = {
    income: { path: "incomes", collection: "incomes", dialogId: "income-dialog", formId: "income-form", singular: "receita", createTitle: "Nova receita", editTitle: "Editar receita", createButton: "Salvar receita" },
    expense: { path: "expenses", collection: "expenses", dialogId: "expense-dialog", formId: "expense-form", singular: "despesa", createTitle: "Nova despesa", editTitle: "Editar despesa", createButton: "Salvar despesa" },
    debt: { path: "debts", collection: "debts", dialogId: "debt-dialog", formId: "debt-form", singular: "dívida", createTitle: "Nova dívida", editTitle: "Editar dívida", createButton: "Salvar dívida" },
    agreement: { path: "agreements", collection: "agreements", dialogId: "agreement-dialog", formId: "agreement-form", singular: "acordo", createTitle: "Novo acordo de pagamento", editTitle: "Editar acordo de pagamento", createButton: "Salvar acordo" }
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
    const dateOnly = !includeTime && /^\d{4}-\d{2}-\d{2}$/.test(String(value));
    const date = dateOnly
      ? new Date(Number(value.slice(0, 4)), Number(value.slice(5, 7)) - 1, Number(value.slice(8, 10)))
      : new Date(value);
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

  function canViewManagement() {
    return Boolean(state.user?.is_superuser)
      || (state.user?.permissions || []).includes("report.read");
  }

  function canExportManagement() {
    return Boolean(state.user?.is_superuser)
      || (state.user?.permissions || []).includes("report.export");
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

  function canDeleteClients() {
    return Boolean(state.user?.is_superuser)
      || (state.user?.permissions || []).includes("client.delete");
  }

  function canManageCollectionQueue() {
    return Boolean(state.user?.is_superuser) || ["admin", "supervisor"].includes(String(state.user?.role || ""));
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
    $("#management-nav-item").hidden = !canViewManagement();
    $("#management-export").hidden = !canExportManagement();
    $("#export-clients-button").hidden = !canExportClients();
    $("#import-clients-button").hidden = !canImportClients();
  }

  function setView(view) {
    if (view === "audit" && !canViewAudit()) view = "dashboard";
    if (view === "management" && !canViewManagement()) view = "dashboard";
    if (!viewMeta[view]) return;
    state.currentView = view;
    $$(".page-view").forEach((section) => section.classList.toggle("active-view", section.id === `view-${view}`));
    $$(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === (view === "clientDetail" ? "clients" : view)));
    $("#view-kicker").textContent = viewMeta[view][0];
    $("#view-title").textContent = viewMeta[view][1];
    $("#top-action-button").textContent = viewMeta[view][2];
    $("#top-action-button").hidden = ["audit", "collections", "agenda", "management"].includes(view);
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
    if (id === "agreement-dialog") fillAgreementDebtSelect();
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
    closeDialog($("#client-import-final-dialog"));
    form.reset();
    state.clientImport = { filename: "", clients: [], preview: null };
    $("#client-import-summary").hidden = true;
    $("#client-import-preview-body").innerHTML = "";
    $("#client-import-guidance").textContent = "";
    $("#client-import-errors-button").hidden = true;
    $("#client-import-authorization-label").hidden = true;
    $("#client-import-authorization").checked = false;
    const previewButton = $("#client-import-preview-button");
    const confirmButton = $("#client-import-confirm-button");
    previewButton.disabled = false;
    previewButton.textContent = "Conferir arquivo";
    delete previewButton.dataset.originalLabel;
    confirmButton.hidden = true;
    confirmButton.disabled = true;
    confirmButton.textContent = "Importar clientes";
    delete confirmButton.dataset.originalLabel;
    const finalButton = $("#client-import-final-confirm-button");
    finalButton.disabled = false;
    finalButton.textContent = "Confirmar e gravar";
    delete finalButton.dataset.originalLabel;
  }

  function clearClientImportPreview() {
    state.clientImport = { filename: "", clients: [], preview: null };
    $("#client-import-summary").hidden = true;
    $("#client-import-preview-body").innerHTML = "";
    $("#client-import-guidance").textContent = "";
    $("#client-import-errors-button").hidden = true;
    $("#client-import-authorization-label").hidden = true;
    $("#client-import-authorization").checked = false;
    const confirmButton = $("#client-import-confirm-button");
    confirmButton.hidden = true;
    confirmButton.disabled = true;
  }

  function updateClientImportAuthorization() {
    const authorization = $("#client-import-authorization");
    const confirmButton = $("#client-import-confirm-button");
    const hasReadyClients = state.clientImport.clients.length > 0;
    confirmButton.disabled = !hasReadyClients || !authorization.checked;
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
    if (dialogId === "agreement-dialog") updateAgreementInstallmentPreview();
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
      loadCollections(),
      loadOperationalAlerts(),
      loadOperationalAgenda(),
      loadClients(),
      loadCrm(),
      loadUsers(),
      loadSettings(),
      checkHealth()
    ];
    if (state.currentView === "clientDetail" && state.selectedClient) {
      loaders.push(loadClientDetail(state.selectedClient.id));
    }
    if (canViewManagement()) {
      loaders.push(loadManagement());
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

  function managementParams() {
    const params = new URLSearchParams();
    if (state.management.filters.dateFrom) params.set("date_from", state.management.filters.dateFrom);
    if (state.management.filters.dateTo) params.set("date_to", state.management.filters.dateTo);
    return params;
  }

  function comparisonText(currentValue, previousValue, currency = false) {
    const current = Number(currentValue || 0);
    const previous = Number(previousValue || 0);
    if (current === 0 && previous === 0) return { text: "Sem movimento nos dois períodos", tone: "neutral" };
    if (previous === 0) return { text: `Novo resultado no período${currency ? `: ${formatCurrency(current)}` : ""}`, tone: "positive" };
    const variation = ((current - previous) / Math.abs(previous)) * 100;
    const prefix = variation > 0 ? "+" : "";
    return {
      text: `${prefix}${variation.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}% em relação ao período anterior`,
      tone: variation > 0 ? "positive" : variation < 0 ? "negative" : "neutral"
    };
  }

  function renderManagementComparison(selector, current, previous, currency = false) {
    const element = $(selector);
    const result = comparisonText(current, previous, currency);
    element.textContent = result.text;
    element.className = `management-comparison ${result.tone}`;
  }

  async function loadManagement(showNotice = false) {
    const query = managementParams().toString();
    state.management.report = await api(`/api/v1/financial/executive-overview${query ? `?${query}` : ""}`);
    renderManagement();
    if (showNotice) toast("Indicadores gerenciais atualizados.");
  }

  function renderManagement() {
    const report = state.management.report || {};
    $("#management-new-clients").textContent = report.new_clients || 0;
    $("#management-interactions").textContent = report.interactions || 0;
    $("#management-completed-tasks").textContent = report.completed_tasks || 0;
    $("#management-received").textContent = formatCurrency(report.received_amount);
    $("#management-conversion").textContent = `${Number(report.conversion_rate || 0).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
    $("#management-recovery").textContent = `${Number(report.recovery_rate || 0).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
    $("#management-conversion-detail").textContent = `${report.won_count || 0} ganha(s) · ${report.lost_count || 0} perdida(s)`;
    $("#management-recovery-detail").textContent = `${formatCurrency(report.received_amount)} de ${formatCurrency(report.due_amount)}`;
    renderManagementComparison("#management-new-clients-change", report.new_clients, report.previous_new_clients);
    renderManagementComparison("#management-interactions-change", report.interactions, report.previous_interactions);
    renderManagementComparison("#management-completed-tasks-change", report.completed_tasks, report.previous_completed_tasks);
    renderManagementComparison("#management-received-change", report.received_amount, report.previous_received_amount, true);
    $("#management-period-label").textContent = `${formatDate(report.date_from)} a ${formatDate(report.date_to)}`;
    $("#management-overdue-tasks").textContent = report.overdue_tasks || 0;
    $("#management-pending-tasks").textContent = report.pending_tasks || 0;
    $("#management-overdue-collections").textContent = report.overdue_collections || 0;
    $("#management-overdue-amount").textContent = formatCurrency(report.overdue_amount);
    $("#management-open-pipeline").textContent = formatCurrency(report.open_pipeline_value);
    $("#management-weighted-pipeline").textContent = `${formatCurrency(report.weighted_pipeline_value)} ponderado`;

    const trend = Array.isArray(report.trend) ? report.trend : [];
    const maxActivity = Math.max(1, ...trend.map((row) => Math.max(Number(row.new_clients || 0), Number(row.interactions || 0), Number(row.completed_tasks || 0))));
    const maxReceived = Math.max(1, ...trend.map((row) => Number(row.received_amount || 0)));
    $("#management-trend").innerHTML = trend.length ? `<div class="management-trend-track">${trend.map((row) => `<article title="${escapeHtml(formatDate(row.day))}">
      <div class="management-bars"><span class="clients" style="height:${Number(row.new_clients || 0) ? Math.max(3, Number(row.new_clients) / maxActivity * 100) : 0}%"></span><span class="interactions" style="height:${Number(row.interactions || 0) ? Math.max(3, Number(row.interactions) / maxActivity * 100) : 0}%"></span><span class="tasks" style="height:${Number(row.completed_tasks || 0) ? Math.max(3, Number(row.completed_tasks) / maxActivity * 100) : 0}%"></span><span class="received" style="height:${Number(row.received_amount || 0) ? Math.max(3, Number(row.received_amount) / maxReceived * 100) : 0}%"></span></div>
      <strong>${String(row.day).slice(8, 10)}</strong><small>${String(row.day).slice(5, 7)}</small></article>`).join("")}</div>` : '<div class="empty-state">Sem movimento neste período.</div>';

    const stageLabelsLocal = { lead: "Leads", qualified: "Qualificação", proposal: "Proposta", negotiation: "Negociação", won: "Ganhas", lost: "Perdidas" };
    const pipeline = Array.isArray(report.pipeline) ? report.pipeline : [];
    const pipelineMax = Math.max(1, ...pipeline.map((row) => Number(row.count || 0)));
    $("#management-pipeline").innerHTML = pipeline.map((row) => `<article class="management-stage ${escapeHtml(row.stage)}"><div><span>${escapeHtml(stageLabelsLocal[row.stage] || row.stage)}</span><strong>${row.count || 0}</strong></div><div class="management-stage-meter"><span style="width:${Number(row.count || 0) / pipelineMax * 100}%"></span></div><small>${formatCurrency(row.amount)}</small></article>`).join("");

    const team = Array.isArray(report.team) ? report.team : [];
    $("#management-team-count").textContent = `${team.length} ${team.length === 1 ? "responsável" : "responsáveis"}`;
    $("#management-team-body").innerHTML = team.length ? team.map((row) => `<tr><td><strong>${escapeHtml(row.user_name)}</strong></td><td>${row.assigned_clients || 0}</td><td>${row.open_opportunities || 0}</td><td>${row.pending_tasks || 0}</td><td>${row.completed_tasks || 0}</td><td>${row.interactions || 0}</td><td>${row.collection_actions || 0}</td></tr>`).join("") : '<tr><td colspan="7" class="empty-cell">Nenhum responsável ativo encontrado.</td></tr>';

    const insights = [];
    if (Number(report.overdue_tasks || 0) > 0) insights.push(`${report.overdue_tasks} tarefa(s) atrasada(s) precisam de priorização.`);
    if (Number(report.overdue_collections || 0) > 0) insights.push(`${report.overdue_collections} cobrança(s) representam ${formatCurrency(report.overdue_amount)} em atraso.`);
    if (Number(report.conversion_rate || 0) < 25 && Number(report.won_count || 0) + Number(report.lost_count || 0) > 0) insights.push("A conversão comercial ficou abaixo de 25% no período.");
    if (Number(report.recovery_rate || 0) < 50 && Number(report.due_amount || 0) > 0) insights.push("O índice de recebimento ficou abaixo de 50% dos vencimentos.");
    if (!insights.length) insights.push("Nenhum risco crítico foi identificado no período selecionado.");
    $("#management-insights").innerHTML = insights.map((item) => `<p>${escapeHtml(item)}</p>`).join("");
  }

  function setManagementPeriod(period) {
    const today = new Date();
    const days = Number(period || 30);
    const start = new Date(today);
    start.setDate(start.getDate() - Math.max(0, days - 1));
    state.management.filters.period = String(period);
    state.management.filters.dateFrom = localDateValue(start);
    state.management.filters.dateTo = localDateValue(today);
    $("#management-date-from").value = state.management.filters.dateFrom;
    $("#management-date-to").value = state.management.filters.dateTo;
  }

  async function exportManagement() {
    const button = $("#management-export");
    setBusy(button, true, "Gerando…");
    try {
      const headers = new Headers();
      const access = getTokens().access;
      if (access) headers.set("Authorization", `Bearer ${access}`);
      const query = managementParams().toString();
      const response = await fetch(`${API_BASE}/api/v1/financial/executive-overview.csv${query ? `?${query}` : ""}`, { headers });
      if (!response.ok) throw new Error(await readError(response));
      saveBlob(await response.blob(), `central_gerencial_${state.management.filters.dateFrom}_${state.management.filters.dateTo}.csv`);
      toast("Relatório gerencial exportado.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function loadOperationalAlerts(showNotice = false) {
    const response = await api("/api/v1/financial/operational-alerts");
    state.alerts.total = Number(response.total || 0);
    state.alerts.criticalCount = Number(response.critical_count || 0);
    state.alerts.items = Array.isArray(response.items) ? response.items : [];
    renderOperationalAlerts();
    if (showNotice) toast("Alertas atualizados.");
  }

  async function loadOperationalAgenda(showNotice = false) {
    const filters = state.agenda.filters;
    const params = new URLSearchParams();
    if (filters.dateFrom) params.set("date_from", filters.dateFrom);
    if (filters.dateTo) params.set("date_to", filters.dateTo);
    const response = await api(`/api/v1/financial/operational-agenda?${params.toString()}`);
    state.agenda.summary = response.summary || null;
    state.agenda.workload = Array.isArray(response.workload) ? response.workload : [];
    state.agenda.items = Array.isArray(response.items) ? response.items : [];
    renderOperationalAgenda();
    if (showNotice) toast("Agenda atualizada.");
  }

  function renderOperationalAgenda() {
    const summary = state.agenda.summary || {};
    $("#agenda-total").textContent = summary.total || 0;
    $("#agenda-overdue").textContent = summary.overdue || 0;
    $("#agenda-today").textContent = summary.today || 0;
    $("#agenda-upcoming").textContent = summary.upcoming || 0;
    const filters = state.agenda.filters;
    const responsibleSelect = $("#agenda-responsible-filter");
    const fixedOptions = '<option value="all">Todos</option><option value="mine">Minha agenda</option><option value="unassigned">Sem responsável</option>';
    responsibleSelect.innerHTML = fixedOptions + state.agenda.workload.filter((row) => row.user_id).map((row) => `<option value="${escapeHtml(row.user_id)}">${escapeHtml(row.user_name)}</option>`).join("");
    responsibleSelect.value = filters.responsible;
    const items = state.agenda.items.filter((item) =>
      (!filters.search || [item.title, item.client_name, item.assigned_user_name].some((value) => String(value || "").toLocaleLowerCase("pt-BR").includes(filters.search.toLocaleLowerCase("pt-BR"))))
      && (filters.kind === "all" || item.kind === filters.kind)
      && (filters.status === "all" || item.status === filters.status)
      && (filters.responsible === "all"
        || (filters.responsible === "mine" && String(item.assigned_user_id || "") === String(state.user?.id || ""))
        || (filters.responsible === "unassigned" && !item.assigned_user_id)
        || String(item.assigned_user_id || "") === String(filters.responsible))
    );
    $("#agenda-result-count").textContent = items.length === 1 ? "1 registro" : `${items.length} registros`;
    $("#agenda-task-count").textContent = items.filter((item) => item.kind === "task").length;
    $("#agenda-follow-up-count").textContent = items.filter((item) => item.kind === "follow_up").length;
    $("#agenda-promise-count").textContent = items.filter((item) => item.kind === "promise").length;
    const kindLabels = { task: "Tarefa do CRM", follow_up: "Acompanhamento", promise: "Promessa" };
    const statusLabels = { overdue: "Atrasado", today: "Hoje", upcoming: "Próximo" };
    $("#agenda-list").innerHTML = items.length ? items.map((item) => `<article class="agenda-item ${escapeHtml(item.status)}"><button class="agenda-open" type="button" data-agenda-id="${escapeHtml(item.id)}">
      <span class="agenda-date"><strong>${escapeHtml(formatDate(item.due_at, true))}</strong><small>${escapeHtml(statusLabels[item.status] || item.status)}</small></span>
      <span class="agenda-marker" aria-hidden="true"></span>
      <span class="agenda-copy"><small>${escapeHtml(kindLabels[item.kind] || item.kind)}</small><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.client_name || "Sem cliente vinculado")} · ${escapeHtml(item.assigned_user_name || "Sem responsável")}</span></span>
      <span class="badge ${item.priority === "urgent" ? "priority-urgent" : `priority-${escapeHtml(item.priority || "normal")}`} ">${escapeHtml(priorityLabels[item.priority] || "Normal")}</span>
      <span class="agenda-arrow" aria-hidden="true">→</span>
    </button>${item.kind === "task" ? `<button class="complete-button agenda-complete-task" type="button" data-agenda-complete-task="${escapeHtml(String(item.id).replace(/^task:/, ""))}">Concluir</button>` : ""}</article>`).join("") : '<div class="empty-state">Nenhum compromisso encontrado com estes filtros.</div>';
    const workload = state.agenda.workload;
    $("#agenda-workload-summary").textContent = `${workload.length} ${workload.length === 1 ? "responsável" : "responsáveis"}`;
    $("#agenda-workload-list").innerHTML = workload.length ? workload.map((row) => `<button type="button" class="agenda-workload-card ${String(filters.responsible) === String(row.user_id || "unassigned") ? "active" : ""}" data-agenda-responsible="${escapeHtml(row.user_id || "unassigned")}">
      <strong>${escapeHtml(row.user_name)}</strong><span>${escapeHtml(row.total)} compromisso(s)</span><small>${escapeHtml(row.overdue)} atrasado(s) · ${escapeHtml(row.today)} para hoje · ${escapeHtml(row.upcoming)} próximo(s)</small>
    </button>`).join("") : '<div class="empty-state">Nenhum responsável encontrado.</div>';
    renderAgendaWeek(items);
  }

  function agendaWeekStart(value = new Date()) {
    const result = new Date(value);
    result.setHours(0, 0, 0, 0);
    const day = result.getDay();
    result.setDate(result.getDate() - (day === 0 ? 6 : day - 1));
    return result;
  }

  function renderAgendaWeek(items) {
    const start = state.agenda.weekStart ? new Date(`${state.agenda.weekStart}T12:00:00`) : agendaWeekStart();
    state.agenda.weekStart = localDateValue(start);
    const days = Array.from({ length: 7 }, (_, index) => { const day = new Date(start); day.setDate(day.getDate() + index); return day; });
    const end = days[6];
    $("#agenda-week-title").textContent = `${formatDate(localDateValue(start))} a ${formatDate(localDateValue(end))}`;
    const weekItems = items.filter((item) => { const value = String(item.due_at).slice(0, 10); return value >= localDateValue(start) && value <= localDateValue(end); });
    $("#agenda-calendar-count").textContent = `${weekItems.length} compromisso(s)`;
    const weekDay = new Intl.DateTimeFormat("pt-BR", { weekday: "short" });
    $("#agenda-week-grid").innerHTML = days.map((day) => {
      const key = localDateValue(day);
      const daily = weekItems.filter((item) => String(item.due_at).slice(0, 10) === key);
      const today = key === localDateValue(new Date());
      return `<section class="agenda-day-column ${today ? "today" : ""}"><header><span>${escapeHtml(weekDay.format(day))}</span><strong>${day.getDate()}</strong></header><div>${daily.length ? daily.map((item) => `<button type="button" class="agenda-calendar-item ${escapeHtml(item.status)}" data-agenda-id="${escapeHtml(item.id)}"><small>${escapeHtml(String(formatDate(item.due_at, true)).split(", ")[1] || "")}</small><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.client_name || "Sem cliente")}</span></button>`).join("") : '<p>Sem compromissos</p>'}</div></section>`;
    }).join("");
  }

  function setAgendaViewMode(mode) {
    state.agenda.viewMode = mode;
    $("#agenda-timeline-panel").hidden = mode !== "timeline";
    $("#agenda-calendar-panel").hidden = mode !== "calendar";
    $("#agenda-week-navigation").hidden = mode !== "calendar";
    $("#agenda-timeline-view").classList.toggle("active", mode === "timeline");
    $("#agenda-calendar-view").classList.toggle("active", mode === "calendar");
  }

  function moveAgendaWeek(offset) {
    const start = state.agenda.weekStart ? new Date(`${state.agenda.weekStart}T12:00:00`) : agendaWeekStart();
    start.setDate(start.getDate() + offset * 7);
    state.agenda.weekStart = localDateValue(start);
    renderOperationalAgenda();
  }

  async function openAgendaItem(itemId) {
    const item = state.agenda.items.find((entry) => String(entry.id) === String(itemId));
    if (!item) return;
    if (item.kind === "task") {
      state.crmFilters.search = item.title;
      state.crmFilters.taskStatus = item.status === "overdue" ? "overdue" : "all";
      $("#crm-search").value = state.crmFilters.search;
      $("#crm-task-status-filter").value = state.crmFilters.taskStatus;
      setView("crm");
      const tab = $('.crm-tab[data-crm-tab="tasks"]');
      $$(".crm-tab").forEach((entry) => entry.classList.toggle("active", entry === tab));
      $$(".crm-tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === "crm-tasks"));
      renderCrm();
      return;
    }
    state.collections.filters.q = item.client_name || "";
    if (item.kind === "follow_up") state.collections.filters.followUp = item.status;
    if (item.kind === "promise") state.collections.filters.promise = item.status;
    setView("collections");
    const form = $("#collection-filter-form");
    form.elements.q.value = state.collections.filters.q;
    form.elements.follow_up_filter.value = state.collections.filters.followUp;
    form.elements.promise_filter.value = state.collections.filters.promise;
    await loadCollections();
  }

  function localDateValue(value) {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, "0");
    const day = String(value.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  async function applyAgendaPeriod(period) {
    const today = new Date();
    let dateFrom = "";
    let dateTo = "";
    if (period !== "all") {
      dateFrom = localDateValue(today);
      const end = new Date(today);
      end.setDate(end.getDate() + (period === "today" ? 0 : Number(period) - 1));
      dateTo = localDateValue(end);
    }
    state.agenda.filters.dateFrom = dateFrom;
    state.agenda.filters.dateTo = dateTo;
    const form = $("#agenda-filter-form");
    form.elements.date_from.value = dateFrom;
    form.elements.date_to.value = dateTo;
    $$('[data-agenda-period]').forEach((button) => button.classList.toggle("active", button.dataset.agendaPeriod === period));
    await loadOperationalAgenda();
  }

  async function exportOperationalAgenda() {
    const button = $("#agenda-export-button");
    setBusy(button, true, "Gerando…");
    try {
      const filters = state.agenda.filters;
      const params = new URLSearchParams();
      if (filters.dateFrom) params.set("date_from", filters.dateFrom);
      if (filters.dateTo) params.set("date_to", filters.dateTo);
      if (filters.kind !== "all") params.set("kind", filters.kind);
      if (filters.status !== "all") params.set("status", filters.status);
      if (filters.responsible !== "all") params.set("responsible", filters.responsible);
      const headers = new Headers();
      const access = getTokens().access;
      if (access) headers.set("Authorization", `Bearer ${access}`);
      const response = await fetch(`${API_BASE}/api/v1/financial/operational-agenda.csv?${params.toString()}`, { headers });
      if (!response.ok) throw new Error(await readError(response));
      saveBlob(await response.blob(), `agenda_operacional_${filters.dateFrom || "periodo"}_${filters.dateTo || "completo"}.csv`);
      toast("Agenda exportada em CSV.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function renderOperationalAlerts() {
    const badge = $("#alert-count-badge");
    const button = $("#alert-center-button");
    const total = state.alerts.total || 0;
    badge.textContent = total > 99 ? "99+" : String(total);
    badge.hidden = total === 0;
    button.classList.toggle("has-critical-alerts", state.alerts.criticalCount > 0);
    button.setAttribute("aria-label", total ? `Abrir central de alertas, ${total} pendência(s)` : "Abrir central de alertas, nenhuma pendência");
    const list = $("#alert-list");
    if (!state.alerts.items.length) {
      list.innerHTML = '<div class="alert-empty"><strong>Tudo em dia</strong><span>Nenhum alerta operacional ativo.</span></div>';
      return;
    }
    list.innerHTML = state.alerts.items.map((item) => `<button class="alert-item ${escapeHtml(item.severity)}" type="button" data-alert-view="${escapeHtml(item.target_view)}" data-alert-filter="${escapeHtml(item.target_filter)}">
      <span class="alert-item-count">${escapeHtml(item.count)}</span>
      <span><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.detail)}</small></span>
      <span class="alert-item-arrow" aria-hidden="true">→</span>
    </button>`).join("");
  }

  function setAlertPopover(open) {
    state.alerts.open = Boolean(open);
    $("#alert-popover").hidden = !state.alerts.open;
    $("#alert-center-button").setAttribute("aria-expanded", String(state.alerts.open));
  }

  async function openOperationalAlert(targetView, targetFilter) {
    setAlertPopover(false);
    if (targetView === "collections") {
      const [field, value] = String(targetFilter || "").split(":");
      if (field === "attention") state.collections.filters.attention = value || "all";
      if (field === "promise") state.collections.filters.promise = value || "all";
      if (field === "follow_up") state.collections.filters.followUp = value || "all";
      setView("collections");
      const form = $("#collection-filter-form");
      form.elements.attention_filter.value = state.collections.filters.attention;
      form.elements.promise_filter.value = state.collections.filters.promise;
      form.elements.follow_up_filter.value = state.collections.filters.followUp;
      await loadCollections();
      form.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    if (targetView === "crm") {
      state.crmFilters.taskStatus = targetFilter === "task:overdue" ? "overdue" : "all";
      $("#crm-task-status-filter").value = state.crmFilters.taskStatus;
      setView("crm");
      const taskTab = $('.crm-tab[data-crm-tab="tasks"]');
      $$(".crm-tab").forEach((tab) => tab.classList.toggle("active", tab === taskTab));
      $$(".crm-tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === "crm-tasks"));
      renderCrm();
      $("#crm-task-status-filter").scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function collectionParams() {
    const filters = state.collections.filters;
    const params = new URLSearchParams();
    if (filters.q) params.set("q", filters.q);
    if (filters.status && filters.status !== "all") params.set("status", filters.status);
    if (filters.dueFrom) params.set("due_from", filters.dueFrom);
    if (filters.dueTo) params.set("due_to", filters.dueTo);
    if (filters.followUp && filters.followUp !== "all") params.set("follow_up_filter", filters.followUp);
    if (filters.promise && filters.promise !== "all") params.set("promise_filter", filters.promise);
    if (filters.responsible && filters.responsible !== "all") params.set("responsible_filter", filters.responsible);
    if (filters.priority && filters.priority !== "all") params.set("priority_filter", filters.priority);
    if (filters.aging && filters.aging !== "all") params.set("aging_filter", filters.aging);
    if (filters.attention && filters.attention !== "all") params.set("attention_filter", filters.attention);
    params.set("sort_order", filters.sortOrder || "recommended");
    return params;
  }

  function collectionReportParams() {
    const filters = state.collections.reportFilters;
    const params = new URLSearchParams();
    if (filters.dateFrom) params.set("date_from", filters.dateFrom);
    if (filters.dateTo) params.set("date_to", filters.dateTo);
    return params;
  }

  async function loadCollections(showNotice = false) {
    const [response, report] = await Promise.all([
      api(`/api/v1/financial/collections?${collectionParams().toString()}`),
      api(`/api/v1/financial/collections/report?${collectionReportParams().toString()}`)
    ]);
    state.collections.summary = response.summary || null;
    state.collections.workload = Array.isArray(response.workload) ? response.workload : [];
    state.collections.aging = Array.isArray(response.aging) ? response.aging : [];
    state.collections.items = Array.isArray(response.items) ? response.items : [];
    state.collections.total = Number(response.total || 0);
    state.collections.selectedIds = [];
    state.collections.report = report || null;
    renderCollections();
    renderCollectionReport();
    renderDashboardCollections();
    if (showNotice) toast("Cobranças atualizadas.");
  }

  async function loadClientOptions() {
    const response = await api("/api/v1/clients?limit=1000");
    state.clients = Array.isArray(response) ? response : (response.items || []);
    fillClientSelects();
  }

  function clientPageParams(page = state.clientPage.page) {
    const params = new URLSearchParams({
      page: String(Math.max(1, Number(page) || 1)),
      page_size: String(state.clientPage.pageSize)
    });
    const query = $("#client-search").value.trim();
    const status = $("#client-status-filter").value;
    if (query) params.set("q", query);
    if (status !== "all") params.set("status", status);
    return params;
  }

  async function loadClientPage(page = state.clientPage.page) {
    const requestId = state.clientPage.requestId + 1;
    state.clientPage.requestId = requestId;
    $("#clients-table").innerHTML = '<tr><td colspan="6" class="empty-cell">Carregando clientes…</td></tr>';
    const response = await api(`/api/v1/clients/page?${clientPageParams(page).toString()}`);
    if (requestId !== state.clientPage.requestId) return;
    state.clientPage = {
      ...state.clientPage,
      items: Array.isArray(response.items) ? response.items : [],
      total: Number(response.total || 0),
      page: Number(response.page || 1),
      pageSize: Number(response.page_size || state.clientPage.pageSize),
      pages: Number(response.pages || 0),
      requestId
    };
    renderClients();
  }

  async function loadClients(page = 1) {
    await Promise.all([loadClientOptions(), loadClientPage(page)]);
  }

  async function loadClientDetail(clientId) {
    let client = state.clients.find((item) => String(item.id) === String(clientId));
    if (!client) {
      client = state.clientPage.items.find((item) => String(item.id) === String(clientId));
    }
    if (!client) client = await api(`/api/v1/clients/${clientId}`);
    state.selectedClient = client;

    const paths = [
      `/api/v1/financial/clients/${client.id}/incomes`,
      `/api/v1/financial/clients/${client.id}/expenses`,
      `/api/v1/financial/clients/${client.id}/debts`,
      "/api/v1/financial/creditors",
      `/api/v1/diagnoses/${client.id}/preview`,
      `/api/v1/diagnoses/${client.id}/history?limit=50`,
      `/api/v1/financial/clients/${client.id}/agreements`
    ];
    const results = await Promise.allSettled(paths.map((path) => api(path)));
    const valueAt = (index, fallback) => results[index].status === "fulfilled" ? results[index].value : fallback;
    state.financial = {
      incomes: Array.isArray(valueAt(0, [])) ? valueAt(0, []) : [],
      expenses: Array.isArray(valueAt(1, [])) ? valueAt(1, []) : [],
      debts: Array.isArray(valueAt(2, [])) ? valueAt(2, []) : [],
      creditors: Array.isArray(valueAt(3, [])) ? valueAt(3, []) : [],
      diagnosis: valueAt(4, null),
      history: Array.isArray(valueAt(5, [])) ? valueAt(5, []) : [],
      agreements: Array.isArray(valueAt(6, [])) ? valueAt(6, []) : []
    };
    fillCreditorSelect();
    fillAgreementDebtSelect();
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
    fillCollectionUserSelects();
  }

  function fillCollectionUserSelects() {
    const activeUsers = state.users.filter((user) => String(user.status || "active") === "active");
    const filter = $("#collection-responsible-filter");
    const assignment = $("#collection-assignment-user");
    const bulkAssignment = $("#collection-bulk-assignment-user");
    if (filter) {
      const selected = state.collections.filters.responsible || "all";
      filter.innerHTML = '<option value="all">Todos</option><option value="mine">Minhas cobranças</option><option value="unassigned">Sem responsável</option>' + activeUsers.map((user) =>
        `<option value="${escapeHtml(user.id)}">${escapeHtml(user.full_name || user.email)}</option>`
      ).join("");
      filter.value = Array.from(filter.options).some((option) => option.value === selected) ? selected : "all";
    }
    if (assignment) {
      assignment.innerHTML = '<option value="">Sem responsável</option>' + activeUsers.map((user) =>
        `<option value="${escapeHtml(user.id)}">${escapeHtml(user.full_name || user.email)}</option>`
      ).join("");
    }
    if (bulkAssignment) {
      bulkAssignment.innerHTML = '<option value="__keep__">Manter responsável atual</option><option value="">Remover responsável</option>' + activeUsers.map((user) =>
        `<option value="${escapeHtml(user.id)}">${escapeHtml(user.full_name || user.email)}</option>`
      ).join("");
    }
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

  function collectionStatusClass(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "overdue") return "danger";
    if (["pending", "cancelled"].includes(normalized)) return "neutral";
    return "";
  }

  function collectionStatusLabel(value) {
    return collectionStatusLabels[String(value || "").toLowerCase()] || value || "Pendente";
  }

  function collectionPriorityClass(value) {
    const priority = String(value || "normal").toLowerCase();
    if (priority === "urgent") return "danger";
    if (priority === "high") return "priority-high";
    if (priority === "low") return "neutral";
    return "";
  }

  function renderDashboardCollections() {
    const summary = state.collections.summary || {};
    $("#dashboard-overdue-count").textContent = summary.overdue_count ?? 0;
    $("#dashboard-overdue-amount").textContent = `${formatCurrency(summary.overdue_amount)} em atraso`;
    $("#dashboard-due-soon-count").textContent = summary.due_soon_count ?? 0;
    $("#dashboard-due-soon-amount").textContent = `${formatCurrency(summary.due_soon_amount)} a vencer`;
    $("#dashboard-open-count").textContent = summary.open_count ?? 0;
    $("#dashboard-open-amount").textContent = `${formatCurrency(summary.open_amount)} em aberto`;
    const followUps = Number(summary.follow_up_today_count || 0) + Number(summary.overdue_follow_up_count || 0);
    $("#dashboard-follow-up-count").textContent = followUps;
    $("#dashboard-follow-up-detail").textContent = `${summary.overdue_follow_up_count || 0} atrasado(s), ${summary.follow_up_today_count || 0} hoje · ${summary.overdue_promises_count || 0} promessa(s) vencida(s)`;
    $("#dashboard-collections-alert")?.classList.toggle("has-overdue", Number(summary.overdue_count || 0) > 0);
  }

  function renderCollectionAging() {
    const rows = state.collections.aging || [];
    const grid = $("#collection-aging-grid");
    const activeBucket = state.collections.filters.aging || "all";
    grid.innerHTML = rows.length ? rows.map((row) => `<button class="collection-aging-card${activeBucket === row.bucket ? " active" : ""}" type="button" data-aging-bucket="${escapeHtml(row.bucket)}" data-aging-label="${escapeHtml(row.label)}" aria-pressed="${activeBucket === row.bucket ? "true" : "false"}">
      <span>${escapeHtml(row.label)}</span>
      <strong>${formatCurrency(row.amount)}</strong>
      <small>${row.count === 1 ? "1 cobrança atrasada" : `${escapeHtml(row.count || 0)} cobranças atrasadas`}</small>
    </button>`).join("") : '<div class="loading-row">Nenhuma faixa de atraso disponível.</div>';
    $$("[data-aging-bucket]", grid).forEach((button) => button.addEventListener("click", async () => {
      const bucket = String(button.dataset.agingBucket || "all");
      const label = String(button.dataset.agingLabel || "atraso");
      const form = $("#collection-filter-form");
      state.collections.filters.aging = bucket;
      state.collections.filters.status = "all";
      form.elements.aging_filter.value = bucket;
      form.elements.status.value = "all";
      try {
        await loadCollections();
        form.scrollIntoView({ behavior: "smooth", block: "start" });
        toast(`Faixa de ${label} exibida: ${state.collections.total} cobrança(s).`);
      } catch (error) {
        toast(error.message, "error");
      }
    }));
  }

  function renderCollectionWorkload() {
    const rows = state.collections.workload || [];
    const body = $("#collection-workload-body");
    body.innerHTML = rows.length ? rows.map((row) => `<tr>
      <td><strong>${escapeHtml(row.user_name || "Sem responsável")}</strong></td>
      <td>${escapeHtml(row.open_count || 0)}</td>
      <td><span class="${Number(row.overdue_count || 0) > 0 ? "danger-text" : ""}">${escapeHtml(row.overdue_count || 0)}</span></td>
      <td><span class="${Number(row.urgent_count || 0) > 0 ? "danger-text" : ""}">${escapeHtml(row.urgent_count || 0)}</span></td>
      <td>${formatCurrency(row.open_amount)}</td>
      <td><button class="text-link" type="button" data-workload-user="${escapeHtml(row.user_id || "unassigned")}" data-workload-name="${escapeHtml(row.user_name || "Sem responsável")}">Ver fila</button></td>
    </tr>`).join("") : '<tr><td colspan="6" class="empty-cell">Nenhum responsável ativo encontrado.</td></tr>';
    $$("[data-workload-user]", body).forEach((button) => button.addEventListener("click", async () => {
      const responsible = String(button.dataset.workloadUser || "all");
      const responsibleName = String(button.dataset.workloadName || "responsável");
      state.collections.filters.responsible = responsible;
      const filter = $("#collection-responsible-filter");
      if (Array.from(filter.options).some((option) => option.value === responsible)) filter.value = responsible;
      try {
        await loadCollections();
        $("#collection-filter-form").scrollIntoView({ behavior: "smooth", block: "start" });
        toast(`Fila de ${responsibleName} exibida: ${state.collections.total} cobrança(s).`);
      } catch (error) {
        toast(error.message, "error");
      }
    }));
  }

  function selectableCollectionIds() {
    return state.collections.items
      .filter((item) => !["paid", "cancelled"].includes(item.status))
      .map((item) => String(item.id));
  }

  function updateCollectionBulkToolbar() {
    const canManage = canManageCollectionQueue();
    const toolbar = $("#collection-bulk-toolbar");
    const selected = new Set(state.collections.selectedIds.map(String));
    const selectable = selectableCollectionIds();
    if (toolbar) toolbar.hidden = !canManage;
    $("#collection-selected-count").textContent = selected.size === 1 ? "1 selecionada" : `${selected.size} selecionadas`;
    $("#organize-selected-collections").disabled = !canManage || selected.size === 0;
    $("#distribute-selected-collections").disabled = !canManage || selected.size < 2;
    $("#clear-collection-selection").disabled = selected.size === 0;
    const selectAll = $("#collection-select-all");
    selectAll.disabled = !canManage || selectable.length === 0;
    selectAll.checked = selectable.length > 0 && selectable.every((id) => selected.has(id));
    selectAll.indeterminate = selected.size > 0 && !selectAll.checked;
    $$("[data-collection-select]", $("#collections-table")).forEach((checkbox) => {
      checkbox.checked = selected.has(String(checkbox.dataset.collectionSelect));
    });
  }

  function renderCollections() {
    const summary = state.collections.summary || {};
    const items = state.collections.items || [];
    $("#collection-open-amount").textContent = formatCurrency(summary.open_amount);
    $("#collection-open-count").textContent = `${summary.open_count || 0} parcela(s)`;
    $("#collection-overdue-amount").textContent = formatCurrency(summary.overdue_amount);
    $("#collection-overdue-count").textContent = `${summary.overdue_count || 0} parcela(s)`;
    $("#collection-due-soon-amount").textContent = formatCurrency(summary.due_soon_amount);
    $("#collection-due-soon-count").textContent = `${summary.due_soon_count || 0} parcela(s)`;
    $("#collection-paid-month-amount").textContent = formatCurrency(summary.paid_this_month_amount);
    $("#collection-paid-month-count").textContent = `${summary.paid_this_month_count || 0} pagamento(s)`;
    $("#collection-follow-up-today").textContent = `${summary.follow_up_today_count || 0} acompanhamento(s) para hoje`;
    $("#collection-follow-up-overdue").textContent = `${summary.overdue_follow_up_count || 0} acompanhamento(s) atrasado(s)`;
    $("#collection-follow-up-upcoming").textContent = `${summary.upcoming_follow_up_count || 0} acompanhamento(s) futuro(s)`;
    $("#collection-promise-alert").textContent = `${summary.open_promises_count || 0} promessa(s) aberta(s), ${summary.overdue_promises_count || 0} vencida(s)`;
    $("#collection-urgent-count").textContent = `${summary.urgent_count || 0} cobrança(s) urgente(s)`;
    $("#collection-unassigned-count").textContent = `${summary.unassigned_count || 0} cobrança(s) sem responsável`;
    $("#collection-critical-count").textContent = `${summary.critical_count || 0} cobrança(s) crítica(s)`;
    $("#collection-attention-count").textContent = `${summary.attention_count || 0} exige(m) atenção`;
    $("#collection-result-count").textContent = state.collections.total === 1 ? "1 cobrança" : `${state.collections.total} cobranças`;
    renderCollectionAging();
    renderCollectionWorkload();
    $("#collections-table").innerHTML = items.length ? items.map((item) => `<tr>
      <td class="collection-select-cell">${canManageCollectionQueue() && !["paid", "cancelled"].includes(item.status) ? `<input type="checkbox" data-collection-select="${escapeHtml(item.id)}" aria-label="Selecionar cobrança de ${escapeHtml(item.client_name)}" />` : ""}</td>
      <td><strong>${escapeHtml(item.client_name)}</strong></td>
      <td>${escapeHtml(item.agreement_title)}</td>
      <td>${escapeHtml(item.installment_number)}</td>
      <td>${escapeHtml(formatDate(item.due_date))}</td>
      <td>${formatCurrency(item.status === "paid" ? item.paid_amount : item.amount)}</td>
      <td><span class="badge ${collectionStatusClass(item.status)}">${escapeHtml(collectionStatusLabel(item.status))}</span>${item.status === "paid" && item.paid_at ? `<small class="collection-payment-date">Pago em ${escapeHtml(formatDate(item.paid_at, true))}</small>` : ""}</td>
      <td class="collection-owner-cell"><strong>${escapeHtml(item.assigned_user_name || "Sem responsável")}</strong><span class="badge ${collectionPriorityClass(item.priority)}">${escapeHtml(priorityLabels[item.priority] || "Normal")}</span></td>
      <td class="collection-contact-cell">${item.last_contacted_at ? escapeHtml(formatDate(item.last_contacted_at, true)) : "Sem contato"}<small>${item.action_count || 0} registro(s)${item.next_follow_up_at ? ` · Próximo: ${escapeHtml(formatDate(item.next_follow_up_at, true))}` : ""}</small>${item.latest_promise_date ? `<span class="collection-promise-note">Promessa: ${escapeHtml(formatDate(item.latest_promise_date))}${item.latest_promise_amount ? ` · ${formatCurrency(item.latest_promise_amount)}` : ""}</span>` : ""}</td>
      <td class="collection-recommendation-cell"><span class="badge attention-${escapeHtml(item.attention_level || "routine")}">${escapeHtml(attentionLabels[item.attention_level] || "Rotina")}</span><strong>${escapeHtml(item.recommended_action || "Acompanhar vencimento")}</strong><small>${item.attention_score || 0} pontos${item.overdue_days ? ` · ${escapeHtml(item.overdue_days)} dia(s) em atraso` : ""}</small></td>
      <td><div class="collection-row-actions">${canManageCollectionQueue() ? `<button class="edit-button" type="button" data-collection-assignment="${escapeHtml(item.id)}">Organizar</button>` : ""}${!["paid", "cancelled"].includes(item.status) ? `<button class="primary-link" type="button" data-collection-action="${escapeHtml(item.id)}">Registrar contato</button>` : ""}<button class="text-link" type="button" data-collection-history="${escapeHtml(item.id)}">Histórico</button><button class="text-link" type="button" data-collection-client="${escapeHtml(item.client_id)}">Cliente</button></div></td>
    </tr>`).join("") : '<tr><td colspan="11" class="empty-cell">Nenhuma cobrança encontrada com estes filtros.</td></tr>';
    $$("[data-collection-select]", $("#collections-table")).forEach((checkbox) => checkbox.addEventListener("change", () => {
      const selected = new Set(state.collections.selectedIds.map(String));
      if (checkbox.checked) selected.add(String(checkbox.dataset.collectionSelect));
      else selected.delete(String(checkbox.dataset.collectionSelect));
      state.collections.selectedIds = Array.from(selected);
      updateCollectionBulkToolbar();
    }));
    $$("[data-collection-client]", $("#collections-table")).forEach((button) => button.addEventListener("click", () => openClientDetail(button.dataset.collectionClient)));
    $$("[data-collection-action]", $("#collections-table")).forEach((button) => button.addEventListener("click", () => openCollectionActionDialog(button.dataset.collectionAction, false)));
    $$("[data-collection-history]", $("#collections-table")).forEach((button) => button.addEventListener("click", () => openCollectionActionDialog(button.dataset.collectionHistory, true)));
    $$("[data-collection-assignment]", $("#collections-table")).forEach((button) => button.addEventListener("click", () => openCollectionAssignment(button.dataset.collectionAssignment)));
    updateCollectionBulkToolbar();
  }

  function openNextCollection() {
    const nextItem = state.collections.items.find((item) => !["paid", "cancelled"].includes(item.status));
    if (!nextItem) {
      toast("Nenhuma cobrança pendente foi encontrada nesta fila.", "error");
      return;
    }
    openCollectionActionDialog(nextItem.id, false);
  }

  function openCollectionAssignment(installmentId) {
    if (!canManageCollectionQueue()) return;
    const item = state.collections.items.find((entry) => String(entry.id) === String(installmentId));
    if (!item) return;
    state.collections.selectedAssignmentItem = item;
    const form = $("#collection-assignment-form");
    form.reset();
    form.elements.assigned_user_id.value = item.assigned_user_id || "";
    form.elements.priority.value = item.priority || "normal";
    $("#collection-assignment-description").textContent = `${item.client_name} · ${item.agreement_title} · parcela ${item.installment_number}`;
    $("#collection-assignment-dialog").showModal();
  }

  async function saveCollectionAssignment(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const item = state.collections.selectedAssignmentItem;
    if (!form.reportValidity() || !item) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      await api(`/api/v1/financial/collections/${item.id}/assignment`, {
        method: "PUT",
        body: JSON.stringify({
          assigned_user_id: form.elements.assigned_user_id.value || null,
          priority: form.elements.priority.value
        })
      });
      closeDialog($("#collection-assignment-dialog"));
      state.collections.selectedAssignmentItem = null;
      await loadCollections();
      toast("Fila de cobranças atualizada.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function openBulkCollectionAssignment() {
    if (!canManageCollectionQueue() || !state.collections.selectedIds.length) return;
    const form = $("#collection-bulk-assignment-form");
    form.reset();
    form.elements.assigned_user_id.value = "__keep__";
    form.elements.priority.value = "__keep__";
    const count = state.collections.selectedIds.length;
    $("#collection-bulk-assignment-description").textContent = count === 1
      ? "1 cobrança será organizada. Escolha pelo menos uma alteração."
      : `${count} cobranças serão organizadas. Escolha pelo menos uma alteração.`;
    $("#collection-bulk-assignment-dialog").showModal();
  }

  async function saveBulkCollectionAssignment(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const installmentIds = state.collections.selectedIds.slice();
    if (!form.reportValidity() || !installmentIds.length) return;
    const payload = { installment_ids: installmentIds };
    if (form.elements.assigned_user_id.value !== "__keep__") {
      payload.assigned_user_id = form.elements.assigned_user_id.value || null;
    }
    if (form.elements.priority.value !== "__keep__") {
      payload.priority = form.elements.priority.value;
    }
    if (!("assigned_user_id" in payload) && !("priority" in payload)) {
      toast("Escolha um responsável ou uma prioridade para aplicar.", "error");
      return;
    }
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Aplicando…");
    try {
      const response = await api("/api/v1/financial/collections/assignment/bulk", {
        method: "PUT",
        body: JSON.stringify(payload)
      });
      closeDialog($("#collection-bulk-assignment-dialog"));
      state.collections.selectedIds = [];
      await loadCollections();
      const updated = Number(response.updated_count || installmentIds.length);
      toast(updated === 1 ? "1 cobrança organizada." : `${updated} cobranças organizadas.`);
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function openCollectionDistribution() {
    if (!canManageCollectionQueue() || state.collections.selectedIds.length < 2) return;
    const activeUsers = state.users.filter((user) => String(user.status || "active") === "active");
    if (activeUsers.length < 2) {
      toast("Cadastre pelo menos dois usuários ativos para distribuir a fila.", "error");
      return;
    }
    const form = $("#collection-distribution-form");
    form.reset();
    form.elements.priority.value = "__keep__";
    $("#collection-distribution-description").textContent = `${state.collections.selectedIds.length} cobranças serão distribuídas começando por quem possui a menor carga atual.`;
    $("#collection-distribution-users").innerHTML = activeUsers.map((user) => `<label><input type="checkbox" name="user_ids" value="${escapeHtml(user.id)}" checked /><span><strong>${escapeHtml(user.full_name || user.email)}</strong><small>${escapeHtml(userRoleLabels[user.role] || user.role || "Equipe")}</small></span></label>`).join("");
    $("#collection-distribution-dialog").showModal();
  }

  async function saveCollectionDistribution(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const userIds = $$("input[name='user_ids']:checked", form).map((input) => input.value);
    if (userIds.length < 2) {
      toast("Selecione pelo menos dois responsáveis.", "error");
      return;
    }
    const installmentIds = state.collections.selectedIds.slice();
    if (installmentIds.length < 2) {
      toast("Selecione pelo menos duas cobranças.", "error");
      return;
    }
    const payload = { installment_ids: installmentIds, user_ids: userIds };
    if (form.elements.priority.value !== "__keep__") payload.priority = form.elements.priority.value;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Distribuindo…");
    try {
      const response = await api("/api/v1/financial/collections/distribution/balanced", {
        method: "PUT",
        body: JSON.stringify(payload)
      });
      closeDialog($("#collection-distribution-dialog"));
      state.collections.selectedIds = [];
      await loadCollections();
      const detail = (response.distribution || [])
        .filter((row) => Number(row.assigned_count || 0) > 0)
        .map((row) => `${row.user_name}: ${row.assigned_count}`)
        .join(" · ");
      toast(`Distribuição concluída${detail ? ` — ${detail}` : "."}`);
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function renderCollectionReport() {
    const report = state.collections.report || {};
    const team = Array.isArray(report.team) ? report.team : [];
    $("#report-due-amount").textContent = formatCurrency(report.due_amount);
    $("#report-due-count").textContent = `${report.due_count || 0} parcela(s)`;
    $("#report-received-amount").textContent = formatCurrency(report.received_amount);
    $("#report-received-count").textContent = `${report.received_count || 0} pagamento(s)`;
    $("#report-recovery-rate").textContent = `${Number(report.recovery_rate || 0).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 2 })}%`;
    $("#report-promise-amount").textContent = formatCurrency(report.promise_amount);
    $("#report-promise-count").textContent = `${report.promise_count || 0} promessa(s)`;
    $("#report-action-count").textContent = report.action_count || 0;
    $("#report-client-count").textContent = `${report.contacted_clients || 0} cliente(s) contatado(s)`;
    $("#report-overdue-amount").textContent = formatCurrency(report.overdue_amount);
    $("#report-overdue-count").textContent = `${report.overdue_count || 0} parcela(s)`;
    $("#collection-team-report-body").innerHTML = team.length ? team.map((row) => `<tr>
      <td><strong>${escapeHtml(row.user_name)}</strong></td>
      <td>${row.action_count || 0}</td>
      <td>${row.contacted_clients || 0}</td>
      <td>${row.promise_count || 0}</td>
      <td>${formatCurrency(row.promise_amount)}</td>
      <td>${row.follow_up_count || 0}</td>
    </tr>`).join("") : '<tr><td colspan="6" class="empty-cell">Nenhuma ação de cobrança registrada neste período.</td></tr>';
  }

  async function exportCollectionReport() {
    const button = $("#collection-report-export");
    setBusy(button, true, "Gerando…");
    try {
      const headers = new Headers();
      const access = getTokens().access;
      if (access) headers.set("Authorization", `Bearer ${access}`);
      const query = collectionReportParams().toString();
      const response = await fetch(`${API_BASE}/api/v1/financial/collections/report.csv${query ? `?${query}` : ""}`, { headers });
      if (response.status === 401) {
        clearSession();
        showLogin("Sua sessão expirou. Entre novamente.");
        throw new Error("Sessão expirada.");
      }
      if (!response.ok) throw new Error(await readError(response));
      const from = state.collections.reportFilters.dateFrom || "inicio";
      const to = state.collections.reportFilters.dateTo || "hoje";
      saveBlob(await response.blob(), `relatorio_cobrancas_${from}_${to}.csv`);
      toast("Relatório de cobranças exportado em CSV.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function renderCollectionActionHistory() {
    const actions = state.collections.actions || [];
    $("#collection-action-history").innerHTML = actions.length ? `<div class="collection-history-list">${actions.map((action) => `
      <article class="collection-history-item ${action.cancelled_at ? "cancelled" : ""}">
        <header><strong>${escapeHtml(collectionActionTypeLabels[action.action_type] || action.action_type)} · ${escapeHtml(collectionOutcomeLabels[action.outcome] || action.outcome)}${action.cancelled_at ? '<span class="collection-cancelled-badge">Anulado</span>' : ""}</strong><span>${escapeHtml(formatDate(action.contacted_at, true))}</span></header>
        <p>${escapeHtml(action.notes)}</p>
        ${action.promise_date ? `<p class="collection-history-promise">Promessa: ${escapeHtml(formatDate(action.promise_date))}${action.promise_amount ? ` · ${formatCurrency(action.promise_amount)}` : ""}</p>` : ""}
        ${action.next_follow_up_at ? `<p class="collection-history-meta">Próximo acompanhamento: ${escapeHtml(formatDate(action.next_follow_up_at, true))}</p>` : ""}
        <small class="collection-history-meta">Registrado por ${escapeHtml(action.created_by_name || "Equipe")}</small>
        ${action.cancelled_at ? `<p class="collection-cancellation-reason"><strong>Anulado por ${escapeHtml(action.cancelled_by_name || "Administrador")} em ${escapeHtml(formatDate(action.cancelled_at, true))}:</strong> ${escapeHtml(action.cancellation_reason || "Sem motivo informado")}</p>` : ""}
        ${!action.cancelled_at && (state.user?.role === "admin" || state.user?.is_superuser) ? `<div class="collection-history-actions"><button class="danger-link" type="button" data-cancel-collection-action="${escapeHtml(action.id)}">Anular registro</button></div>` : ""}
      </article>`).join("")}</div>` : '<div class="empty-state">Nenhuma ação de cobrança registrada para esta parcela.</div>';
    $$("[data-cancel-collection-action]", $("#collection-action-history")).forEach((button) => button.addEventListener("click", () => openCollectionCancellation(button.dataset.cancelCollectionAction)));
  }

  function openCollectionCancellation(actionId) {
    state.collections.selectedActionId = actionId;
    const form = $("#collection-cancel-form");
    form.reset();
    $("#collection-cancel-dialog").showModal();
    window.setTimeout(() => form.elements.reason.focus(), 30);
  }

  async function cancelCollectionAction(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity() || !state.collections.selectedActionId || !state.collections.selectedItem) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Anulando…");
    try {
      await api(`/api/v1/financial/collections/actions/${state.collections.selectedActionId}/cancel`, {
        method: "POST",
        body: JSON.stringify({ reason: form.elements.reason.value.trim() })
      });
      closeDialog($("#collection-cancel-dialog"));
      await loadCollectionActionHistory(state.collections.selectedItem.id);
      await loadCollections();
      await loadOperationalAlerts();
      toast("Ação de cobrança anulada.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function loadCollectionActionHistory(installmentId) {
    state.collections.actions = await api(`/api/v1/financial/collections/${installmentId}/actions`);
    renderCollectionActionHistory();
  }

  async function openCollectionActionDialog(installmentId, historyOnly = false) {
    const item = state.collections.items.find((entry) => String(entry.id) === String(installmentId));
    if (!item) return;
    state.collections.selectedItem = item;
    const form = $("#collection-action-form");
    form.reset();
    form.elements.contacted_at.value = toLocalDateTimeValue(new Date());
    $("#collection-action-description").textContent = `${item.client_name} · ${item.agreement_title} · parcela ${item.installment_number}`;
    $("#collection-promise-fields").hidden = true;
    $(".form-grid", form).hidden = historyOnly;
    $('button[type="submit"]', form).hidden = historyOnly;
    $("#collection-action-history").innerHTML = '<div class="loading-row">Carregando histórico…</div>';
    $("#collection-action-dialog").showModal();
    try {
      await loadCollectionActionHistory(installmentId);
    } catch (error) {
      $("#collection-action-history").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    }
  }

  function toggleCollectionPromiseFields() {
    const form = $("#collection-action-form");
    const promised = form.elements.outcome.value === "promise_to_pay";
    $("#collection-promise-fields").hidden = !promised;
    form.elements.promise_date.required = promised;
    if (!promised) {
      form.elements.promise_date.value = "";
      form.elements.promise_amount.value = "";
    }
  }

  async function saveCollectionAction(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity() || !state.collections.selectedItem) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      const data = compactObject(Object.fromEntries(new FormData(form)));
      const payload = {
        action_type: data.action_type,
        outcome: data.outcome,
        contacted_at: new Date(data.contacted_at).toISOString(),
        notes: data.notes,
        promise_date: data.promise_date || null,
        promise_amount: data.promise_amount ? Number(data.promise_amount) : null,
        next_follow_up_at: data.next_follow_up_at ? new Date(data.next_follow_up_at).toISOString() : null
      };
      await api(`/api/v1/financial/collections/${state.collections.selectedItem.id}/actions`, { method: "POST", body: JSON.stringify(payload) });
      await loadCollectionActionHistory(state.collections.selectedItem.id);
      await loadCollections();
      await loadOperationalAlerts();
      toast("Ação de cobrança registrada.");
      form.reset();
      form.elements.contacted_at.value = toLocalDateTimeValue(new Date());
      toggleCollectionPromiseFields();
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function renderClients() {
    const { items: clients, total, page, pageSize, pages } = state.clientPage;
    const first = total ? ((page - 1) * pageSize) + 1 : 0;
    const last = total ? Math.min(total, first + clients.length - 1) : 0;
    $("#client-count").textContent = total === 1
      ? "1 cliente encontrado"
      : `${total} clientes encontrados`;
    $("#client-page-range").textContent = total
      ? `Mostrando ${first}–${last} de ${total}`
      : "Nenhum cliente para mostrar";
    $("#client-page-label").textContent = `Página ${pages ? page : 0} de ${pages}`;
    $("#client-prev-page").disabled = page <= 1 || pages === 0;
    $("#client-next-page").disabled = pages === 0 || page >= pages;
    $("#client-page-size").value = String(pageSize);
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

  let clientSearchTimer = null;
  function queueClientSearch() {
    window.clearTimeout(clientSearchTimer);
    clientSearchTimer = window.setTimeout(() => {
      loadClientPage(1).catch((error) => toast(error.message, "error"));
    }, 350);
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

  function saveBlob(blob, filename) {
    const link = document.createElement("a");
    const objectUrl = URL.createObjectURL(blob);
    link.href = objectUrl;
    link.download = filename;
    link.hidden = true;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  }

  async function downloadClientImportTemplate() {
    if (!canImportClients()) {
      toast("Seu perfil não possui permissão para importar clientes.", "error");
      return;
    }
    const button = $("#client-import-template-button");
    setBusy(button, true, "Baixando…");
    try {
      const headers = new Headers();
      const access = getTokens().access;
      if (access) headers.set("Authorization", `Bearer ${access}`);
      const response = await fetch(`${API_BASE}/api/v1/clients/import/template.csv`, { headers });
      if (response.status === 401) {
        clearSession();
        showLogin("Sua sessão expirou. Entre novamente.");
        throw new Error("Sessão expirada.");
      }
      if (!response.ok) throw new Error(await readError(response));
      saveBlob(await response.blob(), "modelo_importacao_clientes.csv");
      toast("Modelo CSV baixado. Preencha uma linha para cada cliente.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  function importReportCell(value) {
    let text = String(value ?? "");
    if (/^[=+\-@\t\r]/.test(text.trimStart())) text = `'${text}`;
    return `"${text.replace(/"/g, '""')}"`;
  }

  function downloadClientImportErrors() {
    const invalidRows = (state.clientImport.preview?.rows || []).filter((row) => !row.valid);
    if (!invalidRows.length) {
      toast("A conferência não encontrou linhas com problema.");
      return;
    }
    const rows = [
      ["Linha", "Nome", "CPF", "Situação", "Erros"],
      ...invalidRows.map((row) => [
        row.line,
        row.display_name || row.data?.full_name || "",
        row.display_cpf || row.data?.cpf || "",
        row.duplicate ? "Duplicado" : "Inválido",
        (row.errors || []).join(" | ") || "Registro inválido"
      ])
    ];
    const csv = rows.map((row) => row.map(importReportCell).join(";")).join("\r\n");
    const now = new Date();
    const stamp = [
      now.getFullYear(),
      String(now.getMonth() + 1).padStart(2, "0"),
      String(now.getDate()).padStart(2, "0")
    ].join("-");
    saveBlob(new Blob([`\ufeff${csv}\r\n`], { type: "text/csv;charset=utf-8" }), `erros_importacao_clientes_${stamp}.csv`);
    toast(`${invalidRows.length} linha(s) com problema exportada(s).`);
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
    $("#client-import-errors-button").hidden = preview.invalid_rows < 1;
    const authorizationLabel = $("#client-import-authorization-label");
    const authorization = $("#client-import-authorization");
    authorizationLabel.hidden = preview.valid_rows < 1;
    authorization.checked = false;
    const confirmButton = $("#client-import-confirm-button");
    confirmButton.hidden = preview.valid_rows < 1;
    confirmButton.disabled = true;
    confirmButton.textContent = preview.valid_rows === 1
      ? "Importar 1 cliente"
      : `Importar ${preview.valid_rows} clientes`;
    delete confirmButton.dataset.originalLabel;
  }

  async function previewClientImport(event) {
    event.preventDefault();
    const form = $("#client-import-form");
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

  function confirmClientImport() {
    if (!canImportClients() || !state.clientImport.clients.length) return;
    const authorization = $("#client-import-authorization");
    if (!authorization.checked) {
      toast("Marque a autorização depois de revisar os clientes.", "error");
      authorization.focus();
      return;
    }
    const count = state.clientImport.clients.length;
    $("#client-import-final-title").textContent = count === 1
      ? "1 cliente será gravado"
      : `${count} clientes serão gravados`;
    $("#client-import-final-message").textContent = `Arquivo: ${state.clientImport.filename}. As linhas com problema ou CPF duplicado não serão gravadas.`;
    $("#client-import-final-dialog").showModal();
  }

  async function executeClientImport() {
    if (!canImportClients() || !state.clientImport.clients.length || !$("#client-import-authorization").checked) {
      closeDialog($("#client-import-final-dialog"));
      toast("A conferência perdeu a validade. Revise o arquivo novamente.", "error");
      return;
    }
    const button = $("#client-import-final-confirm-button");
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
      closeDialog($("#client-import-final-dialog"));
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

  function fillAgreementDebtSelect() {
    const select = $("#agreement-debt");
    if (!select) return;
    const selected = select.value;
    const options = state.financial.debts.map((debt) => {
      const creditor = creditorName(debt.creditor_id);
      return `<option value="${escapeHtml(debt.id)}">${escapeHtml(debtNatureLabel(debt.nature))} · ${escapeHtml(creditor)} · ${escapeHtml(formatCurrency(debt.current_balance))}</option>`;
    }).join("");
    select.innerHTML = `<option value="">Sem dívida vinculada</option>${options}`;
    setSelectValue(select, selected);
  }

  function creditorName(id) {
    return state.financial.creditors.find((creditor) => String(creditor.id) === String(id))?.legal_name || "Credor não informado";
  }

  function debtNatureLabel(value) {
    return debtNatureLabels[String(value || "").toLowerCase()] || value || "Não informada";
  }

  function paymentMethodLabel(value) {
    return paymentMethodLabels[String(value || "").toLowerCase()] || value || "Não informada";
  }

  function agreementStatusLabel(value) {
    return agreementStatusLabels[String(value || "").toLowerCase()] || value || "Em andamento";
  }

  function agreementStatusClass(value) {
    const normalized = String(value || "").toLowerCase();
    if (["defaulted", "cancelled"].includes(normalized)) return "danger";
    if (["draft", "completed"].includes(normalized)) return "neutral";
    return "";
  }

  function agreementDebtLabel(debtId) {
    const debt = state.financial.debts.find((item) => String(item.id) === String(debtId));
    return debt ? `${debtNatureLabel(debt.nature)} · ${creditorName(debt.creditor_id)}` : "Sem dívida vinculada";
  }

  function installmentStatusLabel(value) {
    return installmentStatusLabels[String(value || "").toLowerCase()] || value || "Pendente";
  }

  function installmentStatusClass(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "overdue") return "danger";
    if (["cancelled", "pending"].includes(normalized)) return "neutral";
    return "";
  }

  function agreementPaymentSummary(agreement) {
    const installments = Array.isArray(agreement.installments) ? agreement.installments : [];
    const paid = installments.reduce((total, item) => total + Number(item.paid_amount || 0), 0);
    const installmentBalance = Math.max(0, Number(agreement.negotiated_amount || 0) - Number(agreement.down_payment || 0));
    return {
      paid,
      remaining: Math.max(0, installmentBalance - paid),
      paidCount: installments.filter((item) => item.status === "paid").length,
      installments
    };
  }

  function renderAgreementCard(agreement) {
    const summary = agreementPaymentSummary(agreement);
    const installmentsBody = summary.installments.length
      ? summary.installments.map((item) => `<tr>
          <td>${escapeHtml(item.installment_number)}</td>
          <td>${escapeHtml(formatDate(item.due_date))}</td>
          <td>${formatCurrency(item.amount)}</td>
          <td><span class="badge ${installmentStatusClass(item.status)}">${escapeHtml(installmentStatusLabel(item.status))}</span></td>
          <td>${item.status === "paid" ? `${formatCurrency(item.paid_amount)}<small>${escapeHtml(formatDate(item.paid_at, true))} · ${escapeHtml(paymentMethodLabel(item.payment_method))}</small>` : "—"}</td>
          <td><span class="financial-actions">${item.status === "paid"
            ? `<button class="delete-button" type="button" data-reverse-installment="${escapeHtml(item.id)}" data-agreement-id="${escapeHtml(agreement.id)}">Estornar</button>`
            : `<button class="edit-button" type="button" data-pay-installment="${escapeHtml(item.id)}" data-agreement-id="${escapeHtml(agreement.id)}">Registrar pagamento</button>`}</span></td>
        </tr>`).join("")
      : '<tr><td colspan="6" class="empty-cell">As parcelas ainda não foram geradas.</td></tr>';
    return `<details class="agreement-item" open>
      <summary>
        <span><strong>${escapeHtml(agreement.title)}</strong><small>${escapeHtml(agreementDebtLabel(agreement.debt_id))}</small></span>
        <span><small>Valor negociado</small><strong>${formatCurrency(agreement.negotiated_amount)}</strong></span>
        <span><small>Recebido</small><strong>${formatCurrency(summary.paid)}</strong></span>
        <span><small>Saldo restante</small><strong>${formatCurrency(summary.remaining)}</strong></span>
        <span><span class="badge ${agreementStatusClass(agreement.status)}">${escapeHtml(agreementStatusLabel(agreement.status))}</span></span>
      </summary>
      <div class="agreement-item-content">
        <div class="agreement-toolbar">
          <p>${summary.paidCount} de ${summary.installments.length || agreement.installment_count} parcela(s) paga(s) · ${escapeHtml(paymentMethodLabel(agreement.payment_method))}</p>
          <span class="financial-actions">${!summary.installments.length ? `<button class="edit-button" type="button" data-generate-installments="${escapeHtml(agreement.id)}">Gerar parcelas</button>` : ""}<button class="edit-button" type="button" data-edit-financial="agreement" data-edit-id="${escapeHtml(agreement.id)}">Editar acordo</button><button class="delete-button" type="button" data-delete-financial="agreement" data-delete-id="${escapeHtml(agreement.id)}">Apagar acordo</button></span>
        </div>
        <div class="table-wrap compact-table installment-table"><table><thead><tr><th>Parcela</th><th>Vencimento</th><th>Valor</th><th>Situação</th><th>Pagamento</th><th>Ações</th></tr></thead><tbody>${installmentsBody}</tbody></table></div>
      </div>
    </details>`;
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
    } else if (kind === "agreement") {
      fillAgreementDebtSelect();
      setSelectValue(form.elements.debt_id, item.debt_id || "");
      form.elements.title.value = item.title || "";
      setSelectValue(form.elements.status, item.status || "active", agreementStatusLabel(item.status));
      setSelectValue(form.elements.payment_method, item.payment_method || "pix", paymentMethodLabel(item.payment_method));
      form.elements.original_amount.value = item.original_amount ?? 0;
      form.elements.negotiated_amount.value = item.negotiated_amount ?? "";
      form.elements.down_payment.value = item.down_payment ?? 0;
      form.elements.installment_count.value = item.installment_count ?? 1;
      form.elements.installment_amount.value = item.installment_amount ?? 0;
      form.elements.first_due_date.value = item.first_due_date || "";
      form.elements.notes.value = item.notes || "";
      updateAgreementInstallmentPreview();
    }
    dialog.showModal();
  }

  function renderClientDetail() {
    const client = state.selectedClient;
    if (!client) return;
    const { incomes, expenses, debts, agreements, diagnosis, history } = state.financial;
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
        <div class="button-row"><span class="badge ${isClosedClientStatus(client.status) ? "neutral" : ""}">${escapeHtml(clientStatusLabel(client.status))}</span><button id="edit-client-button" class="secondary-button" type="button">Editar cadastro</button>${canDeleteClients() ? '<button id="delete-client-button" class="danger-button" type="button">Apagar cliente</button>' : ""}</div>
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

      <section class="panel agreement-panel">
        <div class="panel-header"><div><p class="eyebrow dark">NEGOCIAÇÃO</p><h3>Acordos de pagamento</h3></div><div class="button-row"><span class="result-count">${agreements.length} ${agreements.length === 1 ? "acordo" : "acordos"}</span><button class="primary-button" type="button" data-open-dialog="agreement-dialog">Novo acordo</button></div></div>
        <div class="agreement-list">${agreements.length ? agreements.map(renderAgreementCard).join("") : '<div class="empty-state">Nenhum acordo de pagamento cadastrado.</div>'}</div>
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
    $("#delete-client-button")?.addEventListener("click", deleteSelectedClient);
    $$("[data-open-dialog]", $("#client-detail-content")).forEach((button) => button.addEventListener("click", () => openDialog(button.dataset.openDialog)));
    $$("[data-edit-financial]", $("#client-detail-content")).forEach((button) => button.addEventListener("click", () => openFinancialEditor(button.dataset.editFinancial, button.dataset.editId)));
    $$("[data-delete-financial]", $("#client-detail-content")).forEach((button) => button.addEventListener("click", () => deleteFinancial(button.dataset.deleteFinancial, button.dataset.deleteId, button)));
    $$("[data-generate-installments]", $("#client-detail-content")).forEach((button) => button.addEventListener("click", () => generateInstallments(button.dataset.generateInstallments, button)));
    $$("[data-pay-installment]", $("#client-detail-content")).forEach((button) => button.addEventListener("click", () => openInstallmentPayment(button.dataset.agreementId, button.dataset.payInstallment)));
    $$("[data-reverse-installment]", $("#client-detail-content")).forEach((button) => button.addEventListener("click", () => reverseInstallmentPayment(button.dataset.agreementId, button.dataset.reverseInstallment, button)));
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
    await Promise.all([loadCrm(), loadDashboard(), loadOperationalAlerts(), loadOperationalAgenda()]);
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
      const overdue = item.due_at && new Date(item.due_at) < new Date() && !["completed", "cancelled"].includes(status);
      return matchesCrmSearch(item.title, item.description, clientName(item.client_id), taskStatusLabels[status], priorityLabels[priority])
        && (state.crmFilters.taskStatus === "all" || (state.crmFilters.taskStatus === "overdue" ? overdue : status === state.crmFilters.taskStatus))
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
    const article = kind === "agreement" ? "este" : "esta";
    const confirmed = window.confirm(`Deseja realmente apagar ${article} ${definition.singular}? Esta ação não pode ser desfeita.`);
    if (!confirmed) return;

    setBusy(button, true, "Apagando…");
    try {
      await api(`/api/v1/financial/clients/${state.selectedClient.id}/${definition.path}/${itemId}`, { method: "DELETE" });
      const participle = kind === "agreement" ? "apagado" : "apagada";
      await refreshFinancial(`${definition.singular.charAt(0).toUpperCase()}${definition.singular.slice(1)} ${participle}.`);
    } catch (error) {
      toast(error.message, "error");
      setBusy(button, false);
    }
  }

  async function refreshFinancial(message = "Dados financeiros atualizados.") {
    if (!state.selectedClient) return;
    await loadClientDetail(state.selectedClient.id);
    await Promise.allSettled([loadDashboard(), loadCollections(), loadClients()]);
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

  function calculateAgreementInstallment() {
    const form = $("#agreement-form");
    if (!form) return 0;
    const negotiated = Number(form.elements.negotiated_amount.value || 0);
    const downPayment = Number(form.elements.down_payment.value || 0);
    const installments = Math.max(1, Number(form.elements.installment_count.value || 1));
    return Math.max(0, (negotiated - downPayment) / installments);
  }

  function updateAgreementInstallmentPreview() {
    const form = $("#agreement-form");
    const preview = $("#agreement-installment-preview");
    if (!form || !preview) return;
    const installment = Number(form.elements.installment_amount.value || 0) || calculateAgreementInstallment();
    preview.textContent = `Previsão: ${Math.max(1, Number(form.elements.installment_count.value || 1))} parcela(s) de ${formatCurrency(installment)}.`;
  }

  function applyAgreementCalculation() {
    const form = $("#agreement-form");
    if (!form) return;
    form.elements.installment_amount.value = calculateAgreementInstallment().toFixed(2);
    updateAgreementInstallmentPreview();
  }

  async function submitAgreement(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity() || !state.selectedClient) return;
    const negotiatedAmount = Number(form.elements.negotiated_amount.value || 0);
    const downPayment = Number(form.elements.down_payment.value || 0);
    if (downPayment > negotiatedAmount) {
      toast("A entrada não pode ser maior que o valor negociado.", "error");
      form.elements.down_payment.focus();
      return;
    }
    if (!Number(form.elements.installment_amount.value || 0)) applyAgreementCalculation();
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Salvando…");
    try {
      const raw = Object.fromEntries(new FormData(form));
      const payload = {
        debt_id: raw.debt_id || null,
        title: raw.title.trim(),
        status: raw.status || "active",
        payment_method: raw.payment_method,
        original_amount: Number(raw.original_amount || 0),
        negotiated_amount: Number(raw.negotiated_amount || 0),
        down_payment: Number(raw.down_payment || 0),
        installment_count: Math.max(1, Number(raw.installment_count || 1)),
        installment_amount: Number(form.elements.installment_amount.value || 0),
        first_due_date: raw.first_due_date || null,
        notes: raw.notes || null
      };
      const editing = state.editingFinancial?.kind === "agreement" ? state.editingFinancial : null;
      const suffix = editing ? `/${editing.id}` : "";
      await api(`/api/v1/financial/clients/${state.selectedClient.id}/agreements${suffix}`, {
        method: editing ? "PUT" : "POST",
        body: JSON.stringify(payload)
      });
      closeDialog(form.closest("dialog"));
      await refreshFinancial(editing ? "Acordo atualizado." : "Acordo de pagamento cadastrado.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function generateInstallments(agreementId, button) {
    if (!state.selectedClient || !agreementId) return;
    setBusy(button, true, "Gerando…");
    try {
      await api(`/api/v1/financial/clients/${state.selectedClient.id}/agreements/${agreementId}/installments/generate`, { method: "POST" });
      await refreshFinancial("Parcelas geradas com sucesso.");
    } catch (error) {
      toast(error.message, "error");
      setBusy(button, false);
    }
  }

  function openInstallmentPayment(agreementId, installmentId) {
    const agreement = state.financial.agreements.find((item) => String(item.id) === String(agreementId));
    const installment = agreement?.installments?.find((item) => String(item.id) === String(installmentId));
    const dialog = $("#installment-payment-dialog");
    const form = $("#installment-payment-form");
    if (!agreement || !installment || !dialog || !form) {
      toast("Não foi possível localizar a parcela.", "error");
      return;
    }
    form.reset();
    state.installmentPaymentTarget = { agreementId: agreement.id, installmentId: installment.id };
    form.elements.paid_amount.value = Number(installment.amount || 0).toFixed(2);
    form.elements.paid_at.value = toLocalDateTimeValue(new Date());
    setSelectValue(form.elements.payment_method, agreement.payment_method || "pix", paymentMethodLabel(agreement.payment_method));
    $("#installment-payment-description").textContent = `${agreement.title} · Parcela ${installment.installment_number} · Vencimento ${formatDate(installment.due_date)}`;
    dialog.showModal();
  }

  async function submitInstallmentPayment(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const target = state.installmentPaymentTarget;
    if (!form.reportValidity() || !state.selectedClient || !target) return;
    const button = $('button[type="submit"]', form);
    setBusy(button, true, "Confirmando…");
    try {
      const raw = Object.fromEntries(new FormData(form));
      await api(`/api/v1/financial/clients/${state.selectedClient.id}/agreements/${target.agreementId}/installments/${target.installmentId}/payment`, {
        method: "PUT",
        body: JSON.stringify({
          paid_amount: Number(raw.paid_amount || 0),
          paid_at: new Date(raw.paid_at).toISOString(),
          payment_method: raw.payment_method,
          payment_notes: raw.payment_notes || null
        })
      });
      closeDialog(form.closest("dialog"));
      state.installmentPaymentTarget = null;
      await refreshFinancial("Pagamento registrado com sucesso.");
    } catch (error) {
      toast(error.message, "error");
    } finally {
      setBusy(button, false);
    }
  }

  async function reverseInstallmentPayment(agreementId, installmentId, button) {
    if (!state.selectedClient || !window.confirm("Deseja estornar este pagamento? A parcela voltará a ficar pendente ou atrasada.")) return;
    setBusy(button, true, "Estornando…");
    try {
      await api(`/api/v1/financial/clients/${state.selectedClient.id}/agreements/${agreementId}/installments/${installmentId}/payment`, { method: "DELETE" });
      await refreshFinancial("Pagamento estornado. A parcela voltou a ficar em aberto.");
    } catch (error) {
      toast(error.message, "error");
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

  async function deleteSelectedClient(event) {
    const client = state.selectedClient;
    const button = event.currentTarget;
    if (!client || !canDeleteClients()) {
      toast("Seu perfil não possui permissão para apagar clientes.", "error");
      return;
    }
    const confirmed = window.confirm(
      `Apagar o cliente "${client.full_name}"?\n\nEsta ação só será permitida se ele não possuir registros financeiros, diagnósticos ou vínculos no CRM.`
    );
    if (!confirmed) return;

    setBusy(button, true, "Apagando…");
    try {
      await api(`/api/v1/clients/${client.id}`, { method: "DELETE" });
      state.selectedClient = null;
      await Promise.all([loadClients(), loadDashboard()]);
      setView("clients");
      toast(`Cliente "${client.full_name}" apagado com segurança.`);
    } catch (error) {
      toast(error.message, "error");
    } finally {
      if (document.body.contains(button)) setBusy(button, false);
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
      collections: () => loadCollections(true),
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
    $("#client-search").addEventListener("input", queueClientSearch);
    $("#client-status-filter").addEventListener("change", () => {
      loadClientPage(1).catch((error) => toast(error.message, "error"));
    });
    $("#client-page-size").addEventListener("change", (event) => {
      state.clientPage.pageSize = Number(event.currentTarget.value) || 25;
      loadClientPage(1).catch((error) => toast(error.message, "error"));
    });
    $("#client-prev-page").addEventListener("click", () => {
      loadClientPage(state.clientPage.page - 1).catch((error) => toast(error.message, "error"));
    });
    $("#client-next-page").addEventListener("click", () => {
      loadClientPage(state.clientPage.page + 1).catch((error) => toast(error.message, "error"));
    });
    $("#management-period").addEventListener("change", (event) => {
      const period = event.currentTarget.value;
      if (period !== "custom") {
        setManagementPeriod(period);
        loadManagement().catch((error) => toast(error.message, "error"));
      }
    });
    ["#management-date-from", "#management-date-to"].forEach((selector) => $(selector).addEventListener("change", () => {
      $("#management-period").value = "custom";
    }));
    $("#management-filter-form").addEventListener("submit", (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.currentTarget));
      if (!values.date_from || !values.date_to) {
        toast("Informe as datas inicial e final.", "error");
        return;
      }
      if (values.date_from > values.date_to) {
        toast("A data inicial não pode ser posterior à data final.", "error");
        return;
      }
      state.management.filters = { period: String(values.period || "custom"), dateFrom: String(values.date_from), dateTo: String(values.date_to) };
      loadManagement(true).catch((error) => toast(error.message, "error"));
    });
    $("#management-refresh").addEventListener("click", () => loadManagement(true).catch((error) => toast(error.message, "error")));
    $("#management-export").addEventListener("click", exportManagement);
    $("#collections-refresh").addEventListener("click", () => loadCollections(true).catch((error) => toast(error.message, "error")));
    $("#my-collections-button").addEventListener("click", () => {
      state.collections.filters.responsible = "mine";
      $("#collection-responsible-filter").value = "mine";
      loadCollections().catch((error) => toast(error.message, "error"));
    });
    $("#collection-report-form").addEventListener("submit", (event) => {
      event.preventDefault();
      const raw = Object.fromEntries(new FormData(event.currentTarget));
      if (raw.date_from && raw.date_to && raw.date_from > raw.date_to) {
        toast("A data inicial não pode ser posterior à data final.", "error");
        return;
      }
      state.collections.reportFilters = {
        dateFrom: String(raw.date_from || ""),
        dateTo: String(raw.date_to || "")
      };
      loadCollections().then(() => toast("Relatório gerencial atualizado.")).catch((error) => toast(error.message, "error"));
    });
    $("#collection-report-export").addEventListener("click", exportCollectionReport);
    $("#collection-filter-form").addEventListener("submit", (event) => {
      event.preventDefault();
      const raw = Object.fromEntries(new FormData(event.currentTarget));
      if (raw.due_from && raw.due_to && raw.due_from > raw.due_to) {
        toast("A data inicial não pode ser posterior à data final.", "error");
        return;
      }
      state.collections.filters = {
        q: String(raw.q || "").trim(),
        status: String(raw.status || "all"),
        dueFrom: String(raw.due_from || ""),
        dueTo: String(raw.due_to || ""),
        followUp: String(raw.follow_up_filter || "all"),
        promise: String(raw.promise_filter || "all"),
        responsible: String(raw.responsible_filter || "all"),
        priority: String(raw.priority_filter || "all"),
        aging: String(raw.aging_filter || "all"),
        attention: String(raw.attention_filter || "all"),
        sortOrder: String(raw.sort_order || "recommended")
      };
      loadCollections().catch((error) => toast(error.message, "error"));
    });
    $("#clear-collection-filters").addEventListener("click", () => {
      $("#collection-filter-form").reset();
      state.collections.filters = { q: "", status: "all", dueFrom: "", dueTo: "", followUp: "all", promise: "all", responsible: "all", priority: "all", aging: "all", attention: "all", sortOrder: "recommended" };
      loadCollections().catch((error) => toast(error.message, "error"));
    });
    $("#collection-select-all").addEventListener("change", (event) => {
      state.collections.selectedIds = event.currentTarget.checked ? selectableCollectionIds() : [];
      updateCollectionBulkToolbar();
    });
    $("#clear-collection-selection").addEventListener("click", () => {
      state.collections.selectedIds = [];
      updateCollectionBulkToolbar();
    });
    $("#distribute-selected-collections").addEventListener("click", openCollectionDistribution);
    $("#organize-selected-collections").addEventListener("click", openBulkCollectionAssignment);
    $("#next-collection-button").addEventListener("click", openNextCollection);
    $("#collection-action-outcome").addEventListener("change", toggleCollectionPromiseFields);
    $("#collection-action-form").addEventListener("submit", saveCollectionAction);
    $("#collection-cancel-form").addEventListener("submit", cancelCollectionAction);
    $("#collection-assignment-form").addEventListener("submit", saveCollectionAssignment);
    $("#collection-bulk-assignment-form").addEventListener("submit", saveBulkCollectionAssignment);
    $("#collection-distribution-form").addEventListener("submit", saveCollectionDistribution);
    $("#export-clients-button").addEventListener("click", downloadClientsCsv);
    $("#client-import-form").addEventListener("submit", (event) => event.preventDefault());
    $("#client-import-template-button").addEventListener("click", downloadClientImportTemplate);
    $("#client-import-errors-button").addEventListener("click", downloadClientImportErrors);
    $("#client-import-preview-button").addEventListener("click", previewClientImport);
    $("#client-import-confirm-button").addEventListener("click", confirmClientImport);
    $("#client-import-final-confirm-button").addEventListener("click", executeClientImport);
    $("#client-import-file").addEventListener("change", clearClientImportPreview);
    $("#client-import-authorization").addEventListener("change", updateClientImportAuthorization);
    $("#crm-search").addEventListener("input", (event) => {
      state.crmFilters.search = event.currentTarget.value;
      renderCrm();
    });
    $("#alert-center-button").addEventListener("click", (event) => {
      event.stopPropagation();
      setAlertPopover(!state.alerts.open);
    });
    $("#agenda-filter-form").addEventListener("submit", (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.currentTarget));
      if (values.date_from && values.date_to && values.date_from > values.date_to) {
        toast("A data inicial não pode ser posterior à data final.", "error");
        return;
      }
      state.agenda.filters = { search: String(values.search || "").trim(), kind: values.kind || "all", status: values.status || "all", responsible: values.responsible || "all", dateFrom: values.date_from || "", dateTo: values.date_to || "" };
      loadOperationalAgenda().catch((error) => toast(error.message, "error"));
    });
    $("#agenda-clear-filters").addEventListener("click", () => {
      $("#agenda-filter-form").reset();
      state.agenda.filters = { search: "", kind: "all", status: "all", responsible: "all", dateFrom: "", dateTo: "" };
      loadOperationalAgenda().catch((error) => toast(error.message, "error"));
    });
    $("#agenda-refresh").addEventListener("click", () => loadOperationalAgenda(true).catch((error) => toast(error.message, "error")));
    $("#agenda-new-task").addEventListener("click", () => openDialog("task-dialog"));
    $("#agenda-timeline-view").addEventListener("click", () => setAgendaViewMode("timeline"));
    $("#agenda-calendar-view").addEventListener("click", () => setAgendaViewMode("calendar"));
    $("#agenda-previous-week").addEventListener("click", () => moveAgendaWeek(-1));
    $("#agenda-next-week").addEventListener("click", () => moveAgendaWeek(1));
    $("#agenda-current-week").addEventListener("click", () => { state.agenda.weekStart = localDateValue(agendaWeekStart()); renderOperationalAgenda(); });
    $("#agenda-export-button").addEventListener("click", exportOperationalAgenda);
    $$('[data-agenda-period]').forEach((button) => button.addEventListener("click", () => applyAgendaPeriod(button.dataset.agendaPeriod).catch((error) => toast(error.message, "error"))));
    $("#my-agenda-button").addEventListener("click", () => {
      state.agenda.filters.responsible = "mine";
      $("#agenda-responsible-filter").value = "mine";
      renderOperationalAgenda();
      toast("Sua agenda está sendo exibida.");
    });
    $("#agenda-workload-list").addEventListener("click", (event) => {
      const item = event.target.closest("[data-agenda-responsible]");
      if (!item) return;
      state.agenda.filters.responsible = item.dataset.agendaResponsible;
      $("#agenda-responsible-filter").value = state.agenda.filters.responsible;
      renderOperationalAgenda();
    });
    $("#agenda-list").addEventListener("click", (event) => {
      const complete = event.target.closest("[data-agenda-complete-task]");
      const item = event.target.closest("[data-agenda-id]");
      if (complete) completeCrmTask(complete.dataset.agendaCompleteTask, complete);
      else if (item) openAgendaItem(item.dataset.agendaId).catch((error) => toast(error.message, "error"));
    });
    $("#agenda-week-grid").addEventListener("click", (event) => { const item = event.target.closest("[data-agenda-id]"); if (item) openAgendaItem(item.dataset.agendaId).catch((error) => toast(error.message, "error")); });
    $("#alert-close-button").addEventListener("click", () => setAlertPopover(false));
    $("#alert-refresh-button").addEventListener("click", () => loadOperationalAlerts(true).catch((error) => toast(error.message, "error")));
    $("#alert-list").addEventListener("click", (event) => {
      const item = event.target.closest("[data-alert-view]");
      if (item) openOperationalAlert(item.dataset.alertView, item.dataset.alertFilter).catch((error) => toast(error.message, "error"));
    });
    document.addEventListener("click", (event) => {
      if (state.alerts.open && !event.target.closest(".alert-center")) setAlertPopover(false);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && state.alerts.open) setAlertPopover(false);
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
    $("#agreement-form").addEventListener("submit", submitAgreement);
    $("#installment-payment-form").addEventListener("submit", submitInstallmentPayment);
    $("#agreement-calculate-button").addEventListener("click", applyAgreementCalculation);
    ["negotiated_amount", "down_payment", "installment_count", "installment_amount"].forEach((name) => {
      $("#agreement-form").elements[name].addEventListener("input", updateAgreementInstallmentPreview);
    });
    $("#agreement-debt").addEventListener("change", (event) => {
      if (state.editingFinancial) return;
      const debt = state.financial.debts.find((item) => String(item.id) === String(event.target.value));
      if (!debt) return;
      const form = $("#agreement-form");
      form.elements.title.value = `Acordo com ${creditorName(debt.creditor_id)}`;
      form.elements.original_amount.value = Number(debt.current_balance || 0).toFixed(2);
      if (!form.elements.negotiated_amount.value) form.elements.negotiated_amount.value = Number(debt.current_balance || 0).toFixed(2);
      updateAgreementInstallmentPreview();
    });
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
      if (button.dataset.view === "collections") loadCollections().catch((error) => toast(error.message, "error"));
      if (button.dataset.view === "management") loadManagement().catch((error) => toast(error.message, "error"));
      if (button.dataset.view === "settings") loadSettings().catch((error) => toast(error.message, "error"));
      if (button.dataset.view === "audit" && canViewAudit()) loadAudit(1).catch((error) => toast(error.message, "error"));
    }));
    $$("[data-view-link]").forEach((button) => button.addEventListener("click", () => {
      setView(button.dataset.viewLink);
      if (button.dataset.viewLink === "collections") loadCollections().catch((error) => toast(error.message, "error"));
    }));
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

  function localDateValue(value) {
    return [
      value.getFullYear(),
      String(value.getMonth() + 1).padStart(2, "0"),
      String(value.getDate()).padStart(2, "0")
    ].join("-");
  }

  async function boot() {
    $("#today-date").textContent = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "long" }).format(new Date());
    $("#api-address").textContent = API_BASE || "Não configurada";
    const today = new Date();
    const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
    state.collections.reportFilters = { dateFrom: localDateValue(monthStart), dateTo: localDateValue(today) };
    $("#collection-report-from").value = state.collections.reportFilters.dateFrom;
    $("#collection-report-to").value = state.collections.reportFilters.dateTo;
    setManagementPeriod("30");
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
