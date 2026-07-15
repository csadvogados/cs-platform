from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User

def bootstrap(db: Session) -> None:
    org = db.scalar(select(Organization).limit(1))
    if not org:
        org = Organization(legal_name=settings.initial_organization_name, trade_name="CS Recupera")
        db.add(org); db.flush()
    email = settings.initial_admin_email.lower()
    if not db.scalar(select(User).where(User.email == email)):
        db.add(User(organization_id=org.id, full_name="Administrador CS", email=email, password_hash=hash_password(settings.initial_admin_password), role="admin", is_superuser=True))
    db.commit()
