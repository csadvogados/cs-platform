import logging
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.organization_branding import OrganizationBranding
from app.models.organization_license import OrganizationLicense
from app.models.organization_settings import OrganizationSettings
from app.models.user import User
from app.services.access_control import seed_permissions_and_roles

logger = logging.getLogger("cs_platform.bootstrap")

def bootstrap(db: Session) -> None:
    try:
        organization = db.scalar(
            select(Organization).order_by(Organization.created_at.asc()).limit(1)
        )

        if organization is None:
            organization = Organization(
                legal_name=settings.initial_organization_name,
                trade_name="CS Recupera",
                is_system_default=True,
            )
            db.add(organization)
            db.flush()
            logger.info("Organização inicial criada: %s.", settings.initial_organization_name)

        if organization.settings is None:
            db.add(OrganizationSettings(organization_id=organization.id))
        if organization.branding is None:
            db.add(OrganizationBranding(
                organization_id=organization.id,
                public_name=organization.trade_name or organization.legal_name,
            ))
        if organization.license is None:
            db.add(OrganizationLicense(organization_id=organization.id))

        admin_email = settings.initial_admin_email.strip().lower()
        admin = db.scalar(select(User).where(User.email == admin_email))

        if admin is None:
            admin = User(
                organization_id=organization.id,
                full_name="Administrador CS",
                email=admin_email,
                password_hash=hash_password(settings.initial_admin_password),
                role="admin",
                status="active",
                is_superuser=True,
                must_change_password=True,
                failed_login_attempts=0,
                locked_until=None,
            )
            db.add(admin)
            logger.info("Administrador inicial criado: %s.", admin_email)

        elif settings.reset_admin_on_startup:
            new_password = (
                settings.reset_admin_password.strip()
                or settings.initial_admin_password
            )
            if len(new_password) < 12:
                raise RuntimeError(
                    "RESET_ADMIN_PASSWORD deve possuir pelo menos 12 caracteres."
                )
            admin.password_hash = hash_password(new_password)
            admin.failed_login_attempts = 0
            admin.locked_until = None
            admin.status = "active"
            admin.is_superuser = True
            admin.role = "admin"
            admin.must_change_password = False
            logger.warning(
                "RESET_ADMIN_ON_STARTUP habilitado. Senha do administrador %s foi redefinida.",
                admin.email,
            )

        db.flush()
        seed_permissions_and_roles(db, organization.id)
        db.commit()
        logger.info("Bootstrap concluído com sucesso.")

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Erro de banco de dados durante o bootstrap.")
        raise
    except Exception:
        db.rollback()
        logger.exception("Erro inesperado durante o bootstrap.")
        raise
