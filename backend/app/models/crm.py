from __future__ import annotations
from datetime import date, datetime
import uuid
from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class CRMContact(TimestampMixin, Base):
    __tablename__='crm_contacts'
    id: Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('organizations.id',ondelete='CASCADE'),index=True)
    client_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('clients.id',ondelete='CASCADE'),index=True)
    name: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    email: Mapped[str|None]=mapped_column(String(320),index=True)
    phone: Mapped[str|None]=mapped_column(String(40),index=True)
    position: Mapped[str|None]=mapped_column(String(120))
    notes: Mapped[str|None]=mapped_column(Text)

class CRMInteraction(TimestampMixin, Base):
    __tablename__='crm_interactions'
    id: Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('organizations.id',ondelete='CASCADE'),index=True)
    client_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('clients.id',ondelete='CASCADE'),index=True)
    user_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL'),index=True)
    interaction_type: Mapped[str]=mapped_column(String(50),nullable=False,index=True)
    subject: Mapped[str]=mapped_column(String(200),nullable=False)
    description: Mapped[str|None]=mapped_column(Text)
    occurred_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,index=True)

class CRMOpportunity(TimestampMixin, Base):
    __tablename__='crm_opportunities'
    id: Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('organizations.id',ondelete='CASCADE'),index=True)
    client_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('clients.id',ondelete='CASCADE'),index=True)
    owner_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL'),index=True)
    title: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    stage: Mapped[str]=mapped_column(String(50),nullable=False,default='lead',index=True)
    estimated_value: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    probability: Mapped[int]=mapped_column(nullable=False,default=0)
    expected_close_date: Mapped[date|None]=mapped_column(Date)
    notes: Mapped[str|None]=mapped_column(Text)

class CRMTask(TimestampMixin, Base):
    __tablename__='crm_tasks'
    id: Mapped[uuid.UUID]=mapped_column(Uuid,primary_key=True,default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('organizations.id',ondelete='CASCADE'),index=True)
    client_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('clients.id',ondelete='CASCADE'),index=True)
    opportunity_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('crm_opportunities.id',ondelete='CASCADE'),index=True)
    assigned_to_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('users.id',ondelete='SET NULL'),index=True)
    title: Mapped[str]=mapped_column(String(200),nullable=False)
    description: Mapped[str|None]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(40),nullable=False,default='pending',index=True)
    priority: Mapped[str]=mapped_column(String(20),nullable=False,default='normal',index=True)
    due_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),index=True)
    completed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
