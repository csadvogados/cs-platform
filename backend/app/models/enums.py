from enum import StrEnum

class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"

class ClientStatus(StrEnum):
    LEAD = "lead"
    TRIAGE = "triage"
    PROPOSAL = "proposal"
    CONTRACTED = "contracted"
    DOCUMENTS_PENDING = "documents_pending"
    DIAGNOSIS = "diagnosis"
    NEGOTIATION = "negotiation"
    JUDICIAL_REVIEW = "judicial_review"
    JUDICIAL = "judicial"
    AGREEMENT = "agreement"
    CLOSED = "closed"
    CANCELLED = "cancelled"
