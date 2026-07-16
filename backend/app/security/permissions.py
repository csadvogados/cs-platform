from __future__ import annotations

from enum import StrEnum


class PermissionCode(StrEnum):
    # Administração
    ADMIN_ACCESS = "admin.access"
    ORGANIZATION_READ = "organization.read"
    ORGANIZATION_UPDATE = "organization.update"

    # Usuários
    USER_CREATE = "user.create"
    USER_READ = "user.read"
    USER_UPDATE = "user.update"
    USER_DISABLE = "user.disable"
    USER_MANAGE_ROLES = "user.manage_roles"

    # Clientes
    CLIENT_CREATE = "client.create"
    CLIENT_READ = "client.read"
    CLIENT_UPDATE = "client.update"
    CLIENT_DELETE = "client.delete"
    CLIENT_RESTORE = "client.restore"
    CLIENT_EXPORT = "client.export"

    # Financeiro
    CREDITOR_CREATE = "creditor.create"
    CREDITOR_READ = "creditor.read"
    CREDITOR_UPDATE = "creditor.update"

    DEBT_CREATE = "debt.create"
    DEBT_READ = "debt.read"
    DEBT_UPDATE = "debt.update"
    DEBT_DELETE = "debt.delete"

    NEGOTIATION_CREATE = "negotiation.create"
    NEGOTIATION_READ = "negotiation.read"
    NEGOTIATION_UPDATE = "negotiation.update"
    NEGOTIATION_APPROVE = "negotiation.approve"

    # Documentos
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_READ = "document.read"
    DOCUMENT_VALIDATE = "document.validate"
    DOCUMENT_DELETE = "document.delete"

    # Diagnóstico
    DIAGNOSIS_CREATE = "diagnosis.create"
    DIAGNOSIS_READ = "diagnosis.read"
    DIAGNOSIS_UPDATE = "diagnosis.update"
    DIAGNOSIS_APPROVE = "diagnosis.approve"

    # Dashboard e relatórios
    DASHBOARD_READ = "dashboard.read"
    REPORT_READ = "report.read"
    REPORT_EXPORT = "report.export"

    # Auditoria
    AUDIT_READ = "audit.read"

    @classmethod
    def values(cls) -> tuple[str, ...]:
        return tuple(item.value for item in cls)


__all__ = ["PermissionCode"]
