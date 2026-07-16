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
    try:
        organization = db.scalar(
            select(Organization).limit(1)
        )

        if organization is None:
            organization = Organization(
                legal_name=settings.initial_organization_name,
                trade_name="CS Recupera",
            )
            db.add(organization)
            db.flush()

        email = settings.initial_admin_email.strip().lower()
        admin = db.scalar(
            select(User).where(User.email == email)
        )

        if admin is None:
            admin = User(
                organization_id=organization.id,
                full_name="Administrador CS",
                email=email,
                password_hash=hash_password(
                    settings.initial_admin_password
                ),
                role="admin",
                is_superuser=True,
                must_change_password=True,
            )
            db.add(admin)

        db.commit()

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Erro durante o bootstrap inicial.")
        raise
