from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.client import ClientCreate, ClientRead
from app.schemas.leads import LeadCreate, LeadRead


def test_client_read_accepts_legacy_contact_data_but_create_keeps_validation():
    record = ClientRead.model_validate(
        {
            "id": uuid4(),
            "organization_id": uuid4(),
            "full_name": "Cliente legado",
            "cpf": "00000000000",
            "email": "email-antigo-invalido",
        }
    )
    assert record.cpf == "00000000000"

    with pytest.raises(ValidationError):
        ClientCreate(full_name="Cliente novo", cpf="00000000000")


def test_lead_read_accepts_legacy_data_but_create_requires_valid_contact():
    now = datetime.now(timezone.utc)
    record = LeadRead.model_validate(
        {
            "id": uuid4(),
            "organization_id": uuid4(),
            "full_name": "Lead legado",
            "cpf": "00000000000",
            "email": "email-antigo-invalido",
            "source_id": uuid4(),
            "service_type_id": uuid4(),
            "lost_reason": None,
            "lost_notes": None,
            "converted_at": None,
            "client_id": None,
            "recovery_case_id": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    assert record.email == "email-antigo-invalido"

    with pytest.raises(ValidationError):
        LeadCreate(
            full_name="Lead novo",
            cpf="00000000000",
            source_id=uuid4(),
            service_type_id=uuid4(),
        )
