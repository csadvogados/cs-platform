from datetime import datetime, timezone
import uuid

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.recovery import RecoveryCase
from app.models.user import User
from app.security.permissions import PermissionCode
from app.security.rbac import RolePermissionRegistry


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_process(client, token):
    customer = client.post("/api/v1/clients", headers=auth(token), json={
        "full_name": "Cliente Segurança Judicial", "cpf": "11144477735"
    }).json()
    case = client.post("/api/v1/recovery-cases", headers=auth(token), json={"client_id": customer["id"]}).json()
    with SessionLocal() as db:
        model = db.get(RecoveryCase, uuid.UUID(case["id"]))
        model.status = "judicialized"
        model.stage = "closed"
        db.commit()
    process = client.put(f"/api/v1/recovery-cases/{case['id']}/judicial-process", headers=auth(token), json={
        "process_number": "2001234-56.2026.8.26.0100", "court": "TJSP", "status": "decision_issued"
    }).json()
    return case, process


def test_judicial_permission_matrix_is_granular():
    judicial = {
        PermissionCode.JUDICIAL_PROCESS_READ, PermissionCode.JUDICIAL_PROCESS_UPDATE,
        PermissionCode.JUDICIAL_PROCESS_CLOSE, PermissionCode.JUDICIAL_REPORT_READ,
        PermissionCode.JUDICIAL_REPORT_EXPORT,
    }
    for role in ("admin", "supervisor", "advogado"):
        assert all(RolePermissionRegistry.has_permission(role, permission) for permission in judicial)
    for role in ("atendimento", "financeiro", "negociador", "cliente"):
        assert not RolePermissionRegistry.has_permission(role, PermissionCode.JUDICIAL_PROCESS_UPDATE)
        assert not RolePermissionRegistry.has_permission(role, PermissionCode.JUDICIAL_PROCESS_CLOSE)
        assert not RolePermissionRegistry.has_permission(role, PermissionCode.JUDICIAL_REPORT_READ)


def test_support_cannot_access_judicial_endpoints(client, token):
    case, _ = create_process(client, token)
    created = client.post("/api/v1/users", headers=auth(token), json={
        "full_name": "Atendimento Restrito", "email": "atendimento@example.com",
        "password": "SenhaMuitoForte123!", "role": "atendimento",
    })
    assert created.status_code == 201, created.text
    support_token = create_access_token(created.json()["id"])
    assert client.get(f"/api/v1/recovery-cases/{case['id']}/judicial-process", headers=auth(support_token)).status_code == 403
    assert client.get("/api/v1/judicial-reports/summary", headers=auth(support_token)).status_code == 403


def test_other_organization_cannot_read_judicial_process(client, token):
    case, _ = create_process(client, token)
    with SessionLocal() as db:
        organization = Organization(legal_name="Outro Escritório", trade_name="Outro Escritório")
        db.add(organization)
        db.flush()
        lawyer = User(organization_id=organization.id, full_name="Advogado Externo",
                      email="advogado@outro.example.com", password_hash=hash_password("SenhaMuitoForte123!"),
                      role="advogado", must_change_password=False)
        db.add(lawyer)
        db.commit()
        lawyer_id = lawyer.id
    other_token = create_access_token(str(lawyer_id))
    response = client.get(f"/api/v1/recovery-cases/{case['id']}/judicial-process", headers=auth(other_token))
    assert response.status_code == 404


def test_closed_process_is_immutable(client, token):
    case, process = create_process(client, token)
    closed = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/close", headers=auth(token), json={
        "outcome": "settlement", "closed_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Acordo homologado e cumprido.", "version": process["version"],
    }).json()
    update = client.put(f"/api/v1/recovery-cases/{case['id']}/judicial-process", headers=auth(token), json={
        "process_number": closed["process_number"], "court": closed["court"],
        "status": "appeal", "version": closed["version"],
    })
    assert update.status_code == 409
    event = client.post(f"/api/v1/recovery-cases/{case['id']}/judicial-process/events", headers=auth(token), json={
        "event_date": datetime.now(timezone.utc).isoformat(), "event_type": "note", "title": "Evento indevido"
    })
    assert event.status_code == 409
