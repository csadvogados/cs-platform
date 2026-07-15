import os
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test_cs_platform.db"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"
os.environ["INITIAL_ADMIN_EMAIL"] = "admin@example.com"
os.environ["INITIAL_ADMIN_PASSWORD"] = "StrongPass123!"

import pytest
from fastapi.testclient import TestClient
from app.db.base import Base
from app.db.session import engine
from app.main import app

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def token(client):
    response = client.post("/api/v1/auth/token", data={"username":"admin@example.com","password":"StrongPass123!"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
