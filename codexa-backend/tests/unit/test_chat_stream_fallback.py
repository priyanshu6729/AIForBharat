from __future__ import annotations

from types import SimpleNamespace

import anyio

from app.routers import guidance as guidance_router
from app.schemas.guidance import GuidanceRequest


class _FakeSession:
    def __init__(self):
        self._next_id = 202

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


async def _read_stream(async_iterable) -> str:
    parts: list[str] = []
    async for chunk in async_iterable:
        if isinstance(chunk, bytes):
            parts.append(chunk.decode())
        else:
            parts.append(chunk)
    return "".join(parts)


def test_chat_stream_fallback_emits_chunks_and_done(monkeypatch):
    session = _FakeSession()

    monkeypatch.setattr(
        guidance_router,
        "_get_or_create_user",
        lambda _session, _claims: SimpleNamespace(id=1),
    )
    monkeypatch.setattr(guidance_router, "_load_conversation_history", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(guidance_router, "_safe_save_guidance_log", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(guidance_router, "_log_mentor_outcome", lambda **_kwargs: None)
    monkeypatch.setattr(
        guidance_router,
        "route_chat_stream",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("stream failure")),
    )
    monkeypatch.setattr(guidance_router.settings, "mentor_stream_fallback_enabled", True)
    monkeypatch.setattr(
        guidance_router.engine,
        "stream_chat_fallback",
        lambda *_args, **_kwargs: iter(["local chunk 1", "local chunk 2"]),
    )

    payload = GuidanceRequest(
        user_question="Teach recursion",
        code_context="def fact(n): return 1 if n <= 1 else n * fact(n-1)",
        ast_context={},
        guidance_level=1,
    )

    response = guidance_router.chat_stream(
        payload=payload,
        claims={"sub": "user-1", "email": "user@example.com"},
        session=session,
    )

    text = anyio.run(_read_stream, response.body_iterator)

    assert "local chunk 1" in text
    assert "local chunk 2" in text
    assert '"done": true' in text
    assert '"session_id": 202' in text
