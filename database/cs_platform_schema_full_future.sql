-- CS Platform / CS Recupera
-- Esquema inicial PostgreSQL
-- Versão 1.0
-- Requer PostgreSQL 15+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS crm;
CREATE SCHEMA IF NOT EXISTS recupera;
CREATE SCHEMA IF NOT EXISTS finance;
CREATE SCHEMA IF NOT EXISTS ops;
CREATE SCHEMA IF NOT EXISTS docs;
CREATE SCHEMA IF NOT EXISTS audit;

-- =========================================================
-- ENUMS
-- =========================================================

CREATE TYPE core.user_status AS ENUM ('active','inactive','blocked','pending');
CREATE TYPE crm.client_status AS ENUM (
  'lead','triage','proposal','contracted','documents_pending',
  'diagnosis','negotiation','judicial_review','judicial',
  'agreement','closed','cancelled'
);
CREATE TYPE recupera.debt_nature AS ENUM (
  'consumer','credit_card','overdraft','personal_loan','payroll_loan',
  'essential_service','secured_debt','real_estate_financing',
  'rural_credit','luxury_high_value','tax','alimony','rent_condo','other'
);
CREATE TYPE recupera.negotiation_status AS ENUM (
  'pending','contacted','awaiting_response','under_negotiation',
  'proposal_received','counterproposal_sent','agreement_pending_signature',
  'agreement_closed','closed_without_agreement','cancelled'
);
CREATE TYPE ops.task_priority AS ENUM ('low','normal','high','urgent');
CREATE TYPE ops.task_status AS ENUM ('open','in_progress','waiting','done','cancelled');
CREATE TYPE finance.payment_status AS ENUM ('pending','paid','overdue','cancelled','refunded');
CREATE TYPE docs.document_status AS ENUM ('requested','received','validated','rejected','expired');

-- =========================================================
-- CORE / MULTI-TENANCY / USERS
-- =========================================================

CREATE TABLE core.organizations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  legal_name VARCHAR(200) NOT NULL,
  trade_name VARCHAR(200),
  tax_id VARCHAR(20),
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE core.users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  full_name VARCHAR(200) NOT NULL,
  email CITEXT NOT NULL,
  password_hash TEXT NOT NULL,
  status core.user_status NOT NULL DEFAULT 'active',
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (organization_id, email)
);

CREATE TABLE core.roles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  code VARCHAR(50) NOT NULL,
  name VARCHAR(100) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (organization_id, code)
);

CREATE TABLE core.permissions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code VARCHAR(100) NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE core.user_roles (
  user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES core.roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE core.role_permissions (
  role_id UUID NOT NULL REFERENCES core.roles(id) ON DELETE CASCADE,
  permission_id UUID NOT NULL REFERENCES core.permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);

-- =========================================================
-- CRM / CLIENTES
-- =========================================================

CREATE TABLE crm.clients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  assigned_user_id UUID REFERENCES core.users(id),
  full_name VARCHAR(200) NOT NULL,
  cpf VARCHAR(11) NOT NULL,
  rg VARCHAR(30),
  birth_date DATE,
  marital_status VARCHAR(30),
  profession VARCHAR(120),
  email CITEXT,
  phone VARCHAR(30),
  whatsapp VARCHAR(30),
  address_line VARCHAR(250),
  city VARCHAR(120),
  state CHAR(2),
  postal_code VARCHAR(10),
  status crm.client_status NOT NULL DEFAULT 'lead',
  source VARCHAR(100),
  person_natural BOOLEAN NOT NULL DEFAULT TRUE,
  good_faith_declared BOOLEAN,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ,
  UNIQUE (organization_id, cpf)
);

CREATE INDEX idx_clients_org_status ON crm.clients(organization_id, status);
CREATE INDEX idx_clients_org_name ON crm.clients(organization_id, full_name);
CREATE INDEX idx_clients_org_phone ON crm.clients(organization_id, phone);

CREATE TABLE crm.client_dependents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_id UUID NOT NULL REFERENCES crm.clients(id) ON DELETE CASCADE,
  name VARCHAR(200),
  relationship VARCHAR(60),
  birth_date DATE,
  disability BOOLEAN NOT NULL DEFAULT FALSE,
  serious_illness BOOLEAN NOT NULL DEFAULT FALSE,
  monthly_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE crm.client_incomes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_id UUID NOT NULL REFERENCES crm.clients(id) ON DELETE CASCADE,
  income_type VARCHAR(60) NOT NULL,
  description VARCHAR(200),
  gross_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (gross_amount >= 0),
  net_amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (net_amount >= 0),
  recurring BOOLEAN NOT NULL DEFAULT TRUE,
  proof_document_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE crm.client_expenses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_id UUID NOT NULL REFERENCES crm.clients(id) ON DELETE CASCADE,
  category VARCHAR(80) NOT NULL,
  description VARCHAR(200),
  amount NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (amount >= 0),
  essential BOOLEAN NOT NULL DEFAULT TRUE,
  recurring BOOLEAN NOT NULL DEFAULT TRUE,
  proof_document_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_income_client ON crm.client_incomes(client_id);
CREATE INDEX idx_expense_client ON crm.client_expenses(client_id);

-- =========================================================
-- CS RECUPERA / CREDORES / DÍVIDAS / DIAGNÓSTICO
-- =========================================================

CREATE TABLE recupera.creditors (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  legal_name VARCHAR(200) NOT NULL,
  trade_name VARCHAR(200),
  cnpj VARCHAR(14),
  category VARCHAR(80),
  sac_phone VARCHAR(30),
  sac_email CITEXT,
  ombudsman_phone VARCHAR(30),
  ombudsman_email CITEXT,
  website TEXT,
  consumer_gov_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (organization_id, legal_name)
);

CREATE TABLE recupera.debts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  client_id UUID NOT NULL REFERENCES crm.clients(id) ON DELETE CASCADE,
  creditor_id UUID REFERENCES recupera.creditors(id),
  contract_number VARCHAR(100),
  nature recupera.debt_nature NOT NULL,
  description VARCHAR(250),
  original_amount NUMERIC(14,2),
  current_balance NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (current_balance >= 0),
  monthly_installment NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (monthly_installment >= 0),
  interest_rate_monthly NUMERIC(9,6),
  start_date DATE,
  maturity_date DATE,
  overdue BOOLEAN NOT NULL DEFAULT FALSE,
  payroll_deduction BOOLEAN NOT NULL DEFAULT FALSE,
  included_in_repayment_plan BOOLEAN,
  exclusion_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_debts_client ON recupera.debts(client_id);
CREATE INDEX idx_debts_creditor ON recupera.debts(creditor_id);
CREATE INDEX idx_debts_org_nature ON recupera.debts(organization_id, nature);

CREATE TABLE recupera.diagnoses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  client_id UUID NOT NULL REFERENCES crm.clients(id) ON DELETE CASCADE,
  version INTEGER NOT NULL DEFAULT 1,
  total_net_income NUMERIC(14,2) NOT NULL DEFAULT 0,
  total_essential_expenses NUMERIC(14,2) NOT NULL DEFAULT 0,
  total_debt_balance NUMERIC(14,2) NOT NULL DEFAULT 0,
  total_monthly_installments NUMERIC(14,2) NOT NULL DEFAULT 0,
  disposable_income NUMERIC(14,2) NOT NULL DEFAULT 0,
  commitment_percentage NUMERIC(7,2) NOT NULL DEFAULT 0,
  minimum_existential_reference NUMERIC(14,2) NOT NULL DEFAULT 600,
  eligibility_score INTEGER NOT NULL DEFAULT 0 CHECK (eligibility_score BETWEEN 0 AND 100),
  eligibility_result VARCHAR(100),
  legal_conclusion TEXT,
  economic_conclusion TEXT,
  reviewed_by_user_id UUID REFERENCES core.users(id),
  reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (client_id, version)
);

CREATE TABLE recupera.diagnosis_requirements (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  diagnosis_id UUID NOT NULL REFERENCES recupera.diagnoses(id) ON DELETE CASCADE,
  requirement_code VARCHAR(80) NOT NULL,
  requirement_label VARCHAR(200) NOT NULL,
  result VARCHAR(30) NOT NULL,
  observation TEXT,
  UNIQUE (diagnosis_id, requirement_code)
);

-- =========================================================
-- NEGOCIAÇÕES / TRATATIVAS / PROTOCOLOS
-- =========================================================

CREATE TABLE recupera.negotiations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  client_id UUID NOT NULL REFERENCES crm.clients(id) ON DELETE CASCADE,
  debt_id UUID REFERENCES recupera.debts(id) ON DELETE SET NULL,
  creditor_id UUID REFERENCES recupera.creditors(id),
  owner_user_id UUID REFERENCES core.users(id),
  status recupera.negotiation_status NOT NULL DEFAULT 'pending',
  priority ops.task_priority NOT NULL DEFAULT 'normal',
  opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ,
  next_action TEXT,
  next_action_due_at TIMESTAMPTZ,
  outcome TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_negotiations_client_status ON recupera.negotiations(client_id, status);
CREATE INDEX idx_negotiations_due ON recupera.negotiations(next_action_due_at)
  WHERE status NOT IN ('agreement_closed','closed_without_agreement','cancelled');

CREATE TABLE recupera.interactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  negotiation_id UUID NOT NULL REFERENCES recupera.negotiations(id) ON DELETE CASCADE,
  performed_by_user_id UUID REFERENCES core.users(id),
  interaction_date TIMESTAMPTZ NOT NULL DEFAULT now(),
  interaction_type VARCHAR(80) NOT NULL,
  channel VARCHAR(50),
  protocol_number VARCHAR(120),
  description TEXT,
  proposal_amount NUMERIC(14,2),
  proposal_installments INTEGER,
  proposal_installment_amount NUMERIC(14,2),
  result TEXT,
  attachment_document_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_interactions_negotiation ON recupera.interactions(negotiation_id, interaction_date DESC);
CREATE INDEX idx_interactions_protocol ON recupera.interactions(protocol_number);

-- =========================================================
-- OPERAÇÕES / TAREFAS / AGENDA
-- =========================================================

CREATE TABLE ops.tasks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  client_id UUID REFERENCES crm.clients(id) ON DELETE CASCADE,
  negotiation_id UUID REFERENCES recupera.negotiations(id) ON DELETE CASCADE,
  assigned_user_id UUID REFERENCES core.users(id),
  title VARCHAR(200) NOT NULL,
  description TEXT,
  priority ops.task_priority NOT NULL DEFAULT 'normal',
  status ops.task_status NOT NULL DEFAULT 'open',
  due_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_by_user_id UUID REFERENCES core.users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tasks_assignee_status_due ON ops.tasks(assigned_user_id, status, due_at);
CREATE INDEX idx_tasks_org_due ON ops.tasks(organization_id, due_at);

CREATE TABLE ops.notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
  title VARCHAR(200) NOT NULL,
  body TEXT,
  read_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================================================
-- FINANCEIRO
-- =========================================================

CREATE TABLE finance.contracts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  client_id UUID NOT NULL REFERENCES crm.clients(id) ON DELETE CASCADE,
  contract_type VARCHAR(60) NOT NULL DEFAULT 'cs_recupera',
  total_amount NUMERIC(14,2) NOT NULL DEFAULT 1500,
  installment_count INTEGER NOT NULL DEFAULT 12,
  installment_amount NUMERIC(14,2) NOT NULL DEFAULT 125,
  judicial_phase_amount NUMERIC(14,2) NOT NULL DEFAULT 3000,
  signed_at TIMESTAMPTZ,
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE finance.installments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  contract_id UUID NOT NULL REFERENCES finance.contracts(id) ON DELETE CASCADE,
  installment_number INTEGER NOT NULL,
  due_date DATE NOT NULL,
  amount NUMERIC(14,2) NOT NULL CHECK (amount >= 0),
  status finance.payment_status NOT NULL DEFAULT 'pending',
  paid_at TIMESTAMPTZ,
  paid_amount NUMERIC(14,2),
  payment_method VARCHAR(50),
  external_reference VARCHAR(150),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (contract_id, installment_number)
);

CREATE INDEX idx_installments_due_status ON finance.installments(due_date, status);

CREATE TABLE finance.receipts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  installment_id UUID NOT NULL REFERENCES finance.installments(id),
  receipt_number VARCHAR(50) NOT NULL UNIQUE,
  issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  document_id UUID
);

-- =========================================================
-- DOCUMENTOS
-- =========================================================

CREATE TABLE docs.documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  client_id UUID REFERENCES crm.clients(id) ON DELETE CASCADE,
  uploaded_by_user_id UUID REFERENCES core.users(id),
  category VARCHAR(80) NOT NULL,
  title VARCHAR(200) NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  storage_key TEXT NOT NULL,
  mime_type VARCHAR(120),
  file_size BIGINT,
  checksum_sha256 VARCHAR(64),
  status docs.document_status NOT NULL DEFAULT 'received',
  version INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_client_category ON docs.documents(client_id, category);
CREATE INDEX idx_documents_checksum ON docs.documents(checksum_sha256);

CREATE TABLE docs.generated_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES core.organizations(id),
  client_id UUID NOT NULL REFERENCES crm.clients(id) ON DELETE CASCADE,
  report_type VARCHAR(80) NOT NULL,
  generated_by_user_id UUID REFERENCES core.users(id),
  document_id UUID REFERENCES docs.documents(id),
  template_version VARCHAR(30),
  generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================================================
-- AUDITORIA
-- =========================================================

CREATE TABLE audit.events (
  id BIGSERIAL PRIMARY KEY,
  organization_id UUID,
  user_id UUID,
  entity_schema VARCHAR(60) NOT NULL,
  entity_table VARCHAR(80) NOT NULL,
  entity_id UUID,
  action VARCHAR(30) NOT NULL,
  old_values JSONB,
  new_values JSONB,
  ip_address INET,
  user_agent TEXT,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_entity ON audit.events(entity_schema, entity_table, entity_id);
CREATE INDEX idx_audit_user_date ON audit.events(user_id, occurred_at DESC);

-- =========================================================
-- FUNÇÕES / TRIGGERS
-- =========================================================

CREATE OR REPLACE FUNCTION core.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
  t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'core.organizations',
    'core.users',
    'crm.clients',
    'recupera.debts',
    'recupera.negotiations',
    'ops.tasks'
  ]
  LOOP
    EXECUTE format(
      'CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %s
       FOR EACH ROW EXECUTE FUNCTION core.set_updated_at()',
      replace(t,'.','_'), t
    );
  END LOOP;
END $$;

CREATE OR REPLACE FUNCTION finance.generate_contract_installments()
RETURNS TRIGGER AS $$
DECLARE
  i INTEGER;
BEGIN
  IF NEW.status = 'active' THEN
    FOR i IN 1..NEW.installment_count LOOP
      INSERT INTO finance.installments(
        contract_id, installment_number, due_date, amount
      )
      VALUES(
        NEW.id,
        i,
        (COALESCE(NEW.signed_at, now())::date + ((i - 1) * INTERVAL '1 month'))::date,
        NEW.installment_amount
      )
      ON CONFLICT (contract_id, installment_number) DO NOTHING;
    END LOOP;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generate_contract_installments
AFTER INSERT ON finance.contracts
FOR EACH ROW EXECUTE FUNCTION finance.generate_contract_installments();

-- =========================================================
-- VIEWS
-- =========================================================

CREATE VIEW recupera.v_client_financial_summary AS
SELECT
  c.id AS client_id,
  c.organization_id,
  COALESCE(i.total_income,0) AS total_income,
  COALESCE(e.total_expenses,0) AS total_expenses,
  COALESCE(d.total_debt_balance,0) AS total_debt_balance,
  COALESCE(d.total_installments,0) AS total_monthly_installments,
  COALESCE(i.total_income,0) - COALESCE(e.total_expenses,0) - COALESCE(d.total_installments,0) AS disposable_income,
  CASE
    WHEN COALESCE(i.total_income,0) = 0 THEN 0
    ELSE ROUND((COALESCE(d.total_installments,0) / i.total_income) * 100, 2)
  END AS commitment_percentage
FROM crm.clients c
LEFT JOIN (
  SELECT client_id, SUM(net_amount) total_income
  FROM crm.client_incomes
  WHERE recurring = TRUE
  GROUP BY client_id
) i ON i.client_id = c.id
LEFT JOIN (
  SELECT client_id, SUM(amount) total_expenses
  FROM crm.client_expenses
  WHERE recurring = TRUE
  GROUP BY client_id
) e ON e.client_id = c.id
LEFT JOIN (
  SELECT client_id,
         SUM(current_balance) total_debt_balance,
         SUM(monthly_installment) total_installments
  FROM recupera.debts
  GROUP BY client_id
) d ON d.client_id = c.id
WHERE c.deleted_at IS NULL;

CREATE VIEW finance.v_contract_balance AS
SELECT
  c.id AS contract_id,
  c.client_id,
  c.total_amount,
  COALESCE(SUM(CASE WHEN i.status='paid' THEN i.paid_amount ELSE 0 END),0) AS amount_paid,
  c.total_amount - COALESCE(SUM(CASE WHEN i.status='paid' THEN i.paid_amount ELSE 0 END),0) AS balance_due,
  GREATEST(
    0,
    c.judicial_phase_amount -
    COALESCE(SUM(CASE WHEN i.status='paid' THEN i.paid_amount ELSE 0 END),0)
  ) AS judicial_phase_balance
FROM finance.contracts c
LEFT JOIN finance.installments i ON i.contract_id = c.id
GROUP BY c.id;

-- =========================================================
-- SEED MÍNIMO
-- =========================================================

INSERT INTO core.permissions(code, description) VALUES
('clients.read','Visualizar clientes'),
('clients.write','Criar e editar clientes'),
('diagnosis.approve','Aprovar diagnóstico'),
('negotiations.write','Registrar negociações'),
('finance.write','Gerenciar financeiro'),
('reports.generate','Gerar relatórios'),
('admin.manage','Administrar sistema')
ON CONFLICT (code) DO NOTHING;
