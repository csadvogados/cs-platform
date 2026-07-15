import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User

logger = logging.getLogger("cs_platform.bootstrap")


def bootstrap(db: Session) -> None:
    """
    Cria a organização e o administrador iniciais quando ainda não existirem.
    Pode ser executado em todos os deploys sem duplicar registros.
    """
    try:
        organization = db.scalar(select(Organization).limit(1))

        if organization is None:
            organization = Organization(
                legal_name=settings.initial_organization_name,
                trade_name="CS Recupera",
            )
            db.add(organization)
            db.flush()
            logger.info(
                "Organização inicial criada: %s.",
                settings.initial_organization_name,
            )

        email = settings.initial_admin_email.strip().lower()
        admin = db.scalar(select(User).where(User.email == email))

        if admin is None:
            admin = User(
                organization_id=organization.id,
                full_name="Administrador CS",
                email=email,
                password_hash=hash_password(settings.initial_admin_password),
                role="admin",
                is_superuser=True,
            )
            db.add(admin)
            logger.info("Administrador inicial criado: %s.", email)

        db.commit()
        logger.info("Bootstrap concluído com sucesso.")

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Erro durante o bootstrap inicial.")
        raise
    except Exception:
        db.rollback()
        logger.exception("Erro inesperado durante o bootstrap inicial.")
        raise
