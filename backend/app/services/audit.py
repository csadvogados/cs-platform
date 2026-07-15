import uuid
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent

def record_audit(db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID | None, entity_type: str, entity_id: uuid.UUID | None, action: str, new_values: dict | None = None) -> None:
    db.add(AuditEvent(organization_id=organization_id, user_id=user_id, entity_type=entity_type, entity_id=entity_id, action=action, new_values=new_values))
