from __future__ import annotations

from types import SimpleNamespace

from app.routers import guidance as guidance_router
from app.schemas.guidance import GuidanceRequest


class _FakeSession:
    def __init__(self):
        self._next_id = 101

    def get(self, *_args, **_kwargs):
        return None

    def add(self, _obj):
        return None

    def commit(self):
        return None

    def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = self._next_id

    def rollback(self):
        return None


def test_guidance_provider_exception_falls_back_without_500(monkeypatch):
    session = _FakeSession()

    monkeypatch.setattr(
        guidance_router,
        "_get_or_create_user",
        lambda _session, _claims: SimpleNamespace(id=1),
    )
    monkeypatch.setattr(guidance_router, "_load_conversation_history", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(guidance_router, "_safe_save_guidance_log", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        guidance_router,
        "route_guidance",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("bedrock outage")),
    )
    monkeypatch.setattr(
        guidance_router.engine,
        "generate",
        lambda *_args, **_kwargs: "fallback guidance answer",
    )

    payload = GuidanceRequest(
        user_question="Explain recursion",
        code_context="def f(n): return 1 if n <= 1 else n * f(n-1)",
        ast_context={},
        guidance_level=2,
    )

    response = guidance_router.guidance(
        payload=payload,
        claims={"sub": "user-1", "email": "user@example.com"},
        session=session,
    )

    assert response.response == "fallback guidance answer"
    assert response.session_id == 101
