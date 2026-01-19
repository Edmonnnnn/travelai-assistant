import os
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

try:
    from fastapi.testclient import TestClient
except Exception:
    TestClient = None

from app.core.policy.risk import assess_risk

if TestClient is not None:
    from app.main import app

    client = TestClient(app)
else:
    from app.api.chat import ChatIn, chat


class _DummyRequest:
    def __init__(self) -> None:
        self.state = SimpleNamespace()
        self.headers = {}


def _call_chat(message: str) -> tuple[int, dict]:
    if TestClient is None:
        payload = ChatIn(message=message)
        response = chat(payload, _DummyRequest())
        return 200, response.model_dump(mode="json")
    response = client.post("/chat", json={"message": message})
    return response.status_code, response.json()


def test_high_risk_ru_requires_review():
    message = "Нужна виза в Шенген"
    if TestClient is None:
        decision = assess_risk(message, 0)
        assert decision.risk_color == "red"
        assert decision.requires_review is True
        return
    status_code, payload = _call_chat(message)
    assert status_code == 200
    assert payload["ok"] is True
    assert payload["risk_color"] == "red"
    assert payload["requires_review"] is True
    assert payload["sources"] == []


def test_chat_high_risk_en_requires_review():
    message = "Need visa for Schengen"
    if TestClient is None:
        decision = assess_risk(message, 0)
        assert decision.risk_color == "red"
        assert decision.requires_review is True
        return
    status_code, payload = _call_chat(message)
    assert status_code == 200
    assert payload["ok"] is True
    assert payload["risk_color"] == "red"
    assert payload["requires_review"] is True
    assert payload["sources"] == []


def test_chat_low_risk_green():
    message = "Привет"
    if TestClient is None:
        decision = assess_risk(message, 0)
        assert decision.risk_color == "green"
        assert decision.requires_review is False
        return
    status_code, payload = _call_chat(message)
    assert status_code == 200
    assert payload["risk_color"] == "green"
    assert payload["requires_review"] is False


def test_chat_sources_array_empty():
    status_code, payload = _call_chat("Hello")
    assert status_code == 200
    assert isinstance(payload.get("sources"), list)
    assert payload["sources"] == []
