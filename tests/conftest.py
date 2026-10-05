import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ.update({"DATABASE_URL": f"sqlite:///{_tmp}/test.db", "SECRET_KEY": "test-secret-key-for-pytest-only-0123456789",
                   "AI_PROVIDER": "groq", "AI_API_KEY": "test-key", "RATE_LIMIT_ENABLED": "false",
                   "UPLOAD_DIR": f"{_tmp}/uploads"})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services import ai_service  # noqa: E402


class FakeProvider:
    name, model = "fake", "fake-model"

    def is_configured(self):
        return True

    def chat(self, messages):
        return "pong"


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(ai_service, "get_provider", lambda: FakeProvider())


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def make_user(client, name="alice"):
    client.post("/auth/register", json={"username": name, "email": f"{name}@example.com", "password": "password123"})
    r = client.post("/auth/login", json={"identifier": name, "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['data']['access_token']}"}


@pytest.fixture
def auth(client):
    return make_user(client, "alice")


@pytest.fixture
def auth2(client):
    return make_user(client, "bob")
