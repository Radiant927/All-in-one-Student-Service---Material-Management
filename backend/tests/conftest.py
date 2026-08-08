import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
TEST_DB = BACKEND_DIR / "data" / "test_inventory.db"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["APP_ENV"] = "development"
os.environ["AUTH_PROVIDER"] = "mock"
os.environ["MOCK_AUTH_ENABLED"] = "true"
os.environ["JWT_SECRET"] = "test-secret-at-least-32-characters-long"
os.environ["REPORT_SCHEDULE"] = "disabled"

from database import Base, engine  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


def login(client, subject, name, role="student", student_no=None):
    response = client.post("/api/auth/login", json={
        "external_subject": subject,
        "student_no": student_no,
        "name": name,
        "role": role,
    })
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    return {"Authorization": f"Bearer {data['access_token']}"}, data

