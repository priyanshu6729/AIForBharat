from __future__ import annotations

import pytest

from app.services import model_router


def test_route_chat_first_model_fails_second_succeeds(monkeypatch):
    monkeypatch.setattr(model_router.settings, "mentor_model_order", "bedrock,local")
    monkeypatch.setattr(model_router.settings, "mentor_bedrock_models", "model-primary,model-secondary")

    calls: list[str] = []

    def fake_chat_with_nova(*, model_id=None, **kwargs):
        calls.append(model_id)
        if model_id == "model-primary":
            raise RuntimeError("primary unavailable")
        return "secondary model response"

    monkeypatch.setattr(model_router, "chat_with_nova", fake_chat_with_nova)
    monkeypatch.setattr(
        model_router,
        "normalize_bedrock_error",
        lambda exc: {
            "recoverable": True,
            "category": "model_not_found",
            "message": str(exc),
            "exception_class": exc.__class__.__name__,
        },
    )
    monkeypatch.setattr(
        model_router.engine,
        "generate_chat_fallback",
        lambda *_args, **_kwargs: pytest.fail("local fallback should not run"),
    )

    response, meta = model_router.route_chat(
        question="Explain recursion",
        code_context="",
        conversation_history=[],
    )

    assert response == "secondary model response"
    assert calls == ["model-primary", "model-secondary"]
    assert meta["selected_source"] == "bedrock"
    assert meta["selected_model"] == "model-secondary"
    assert meta["fallback_used"] is False


def test_route_chat_all_bedrock_fail_falls_back_local(monkeypatch):
    monkeypatch.setattr(model_router.settings, "mentor_model_order", "bedrock")
    monkeypatch.setattr(model_router.settings, "mentor_bedrock_models", "bad-1,bad-2")
    monkeypatch.setattr(
        model_router,
        "chat_with_nova",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("provider down")),
    )
    monkeypatch.setattr(
        model_router,
        "normalize_bedrock_error",
        lambda exc: {
            "recoverable": True,
            "category": "timeout_network",
            "message": str(exc),
            "exception_class": exc.__class__.__name__,
        },
    )
    monkeypatch.setattr(
        model_router.engine,
        "generate_chat_fallback",
        lambda *_args, **_kwargs: "local fallback response",
    )

    response, meta = model_router.route_chat(
        question="What is a stack?",
        code_context="",
        conversation_history=[],
    )

    assert response == "local fallback response"
    assert meta["selected_source"] == "local"
    assert meta["fallback_used"] is True
    assert meta["attempt_count"] == 3  # ✅ 2 bedrock + 1 local (local always appended by _iter_model_order)
    assert meta["attempted_models"] == ["bad-1", "bad-2"]  # ✅ only bedrock models tracked here
