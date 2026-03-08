from __future__ import annotations

import time
from typing import Generator

from app.core.config import settings
from app.services.nlp_engine import engine
from app.services.nova_client import (
    chat_with_nova,
    guidance_with_nova,
    normalize_bedrock_error,
    stream_chat_with_nova,
)

class ModelRouterError(RuntimeError):
    """Raised when all configured model routes fail."""


def _error_summary(exc: Exception) -> dict[str, str]:
    normalized = normalize_bedrock_error(exc)
    return {
        "class": normalized.get("exception_class") or exc.__class__.__name__,
        "category": normalized.get("category") or "unknown",
        "message": normalized.get("message") or str(exc),
    }


def _build_meta(
    *,
    start: float,
    attempted_models: list[str],
    attempt_count: int,
    final_source: str,
    final_model: str,
    fallback_used: bool,
    last_error: dict[str, str] | None,
    stream_interrupted: bool = False,
) -> dict:
    return {
        "selected_source": final_source,
        "selected_model": final_model,
        "attempt_count": attempt_count,
        "attempted_models": attempted_models,
        "fallback_used": fallback_used,
        "last_error": last_error,
        "stream_interrupted": stream_interrupted,
        "latency_ms": int((time.perf_counter() - start) * 1000),
    }


def _iter_model_order() -> list[str]:
    order = settings.parsed_mentor_model_order
    if "local" not in order:
        order = [*order, "local"]
    return order


def route_guidance(
    *,
    question: str,
    code: str,
    ast: dict,
    goal: str | None = None,
    guidance_level: int = 0,
    explicit_full: bool = False,
    conversation_history: list[dict] | None = None,
) -> tuple[str, dict]:
    """Route guidance calls across configured model providers with local fallback."""
    start = time.perf_counter()
    attempted_models: list[str] = []
    attempt_count = 0
    last_error: dict[str, str] | None = None

    for source in _iter_model_order():
        if source == "bedrock":
            for model_id in settings.parsed_mentor_bedrock_models:
                attempt_count += 1
                attempted_models.append(model_id)
                try:
                    response = guidance_with_nova(
                        question=question,
                        code=code,
                        ast=ast,
                        goal=goal,
                        guidance_level=guidance_level,
                        explicit_full=explicit_full,
                        conversation_history=conversation_history,
                        model_id=model_id,
                    )
                    if response:
                        return response, _build_meta(
                            start=start,
                            attempted_models=attempted_models,
                            attempt_count=attempt_count,
                            final_source="bedrock",
                            final_model=model_id,
                            fallback_used=False,
                            last_error=last_error,
                        )
                    last_error = {
                        "class": "EmptyResponse",
                        "category": "provider_error",
                        "message": f"Empty guidance response from model {model_id}",
                    }
                except Exception as exc:
                    normalized = normalize_bedrock_error(exc)
                    last_error = _error_summary(exc)
                    # Always continue to next model — never raise mid-loop
                    # Non-recoverable errors (e.g. auth failures) should still
                    # try remaining models and local fallback before giving up
                    continue

        if source == "local":
            attempt_count += 1
            response = engine.generate(
                question,
                code,
                ast,
                goal,
                guidance_level,
            )
            if response:
                return response, _build_meta(
                    start=start,
                    attempted_models=attempted_models,
                    attempt_count=attempt_count,
                    final_source="local",
                    final_model=settings.mentor_local_chat_fallback_mode,
                    fallback_used=bool(attempted_models),
                    last_error=last_error,
                )
            last_error = {
                "class": "EmptyResponse",
                "category": "local_error",
                "message": "Local guidance fallback returned empty response",
            }

    raise ModelRouterError("All mentor guidance routes failed")


def route_chat(
    *,
    question: str,
    code_context: str | None = None,
    conversation_history: list[dict] | None = None,
) -> tuple[str, dict]:
    """Route chat calls across configured model providers with local fallback."""
    start = time.perf_counter()
    attempted_models: list[str] = []
    attempt_count = 0
    last_error: dict[str, str] | None = None

    for source in _iter_model_order():
        if source == "bedrock":
            for model_id in settings.parsed_mentor_bedrock_models:
                attempt_count += 1
                attempted_models.append(model_id)
                try:
                    response = chat_with_nova(
                        question=question,
                        code=code_context,
                        conversation_history=conversation_history,
                        model_id=model_id,
                    )
                    if response:
                        return response, _build_meta(
                            start=start,
                            attempted_models=attempted_models,
                            attempt_count=attempt_count,
                            final_source="bedrock",
                            final_model=model_id,
                            fallback_used=False,
                            last_error=last_error,
                        )
                    last_error = {
                        "class": "EmptyResponse",
                        "category": "provider_error",
                        "message": f"Empty chat response from model {model_id}",
                    }
                except Exception as exc:
                    normalized = normalize_bedrock_error(exc)
                    last_error = _error_summary(exc)
                    # Always continue to next model — never raise mid-loop
                    # Non-recoverable errors (e.g. auth failures) should still
                    # try remaining models and local fallback before giving up
                    continue

        if source == "local":
            attempt_count += 1
            response = engine.generate_chat_fallback(question, code_context)
            if response:
                return response, _build_meta(
                    start=start,
                    attempted_models=attempted_models,
                    attempt_count=attempt_count,
                    final_source="local",
                    final_model=settings.mentor_local_chat_fallback_mode,
                    fallback_used=bool(attempted_models),
                    last_error=last_error,
                )
            last_error = {
                "class": "EmptyResponse",
                "category": "local_error",
                "message": "Local chat fallback returned empty response",
            }

    raise ModelRouterError("All mentor chat routes failed")


def route_chat_stream(
    *,
    question: str,
    code_context: str | None = None,
    conversation_history: list[dict] | None = None,
) -> Generator[tuple[str, dict], None, None]:
    """
    Stream chat with routing/fallback.

    Yields:
      ("chunk", {"text": ...}) for response text chunks
      ("meta", {...}) once at stream completion/finalization
    """
    start = time.perf_counter()
    attempted_models: list[str] = []
    attempt_count = 0
    last_error: dict[str, str] | None = None

    for source in _iter_model_order():
        if source == "bedrock":
            for model_id in settings.parsed_mentor_bedrock_models:
                attempt_count += 1
                attempted_models.append(model_id)
                chunk_count = 0
                try:
                    for chunk in stream_chat_with_nova(
                        question=question,
                        code=code_context,
                        conversation_history=conversation_history,
                        model_id=model_id,
                    ):
                        chunk_count += 1
                        yield "chunk", {"text": chunk}

                    if chunk_count == 0:
                        last_error = {
                            "class": "EmptyResponse",
                            "category": "provider_error",
                            "message": f"Empty stream from model {model_id}",
                        }
                        continue

                    yield "meta", _build_meta(
                        start=start,
                        attempted_models=attempted_models,
                        attempt_count=attempt_count,
                        final_source="bedrock",
                        final_model=model_id,
                        fallback_used=False,
                        last_error=last_error,
                    )
                    return

                except Exception as exc:
                    normalized = normalize_bedrock_error(exc)
                    last_error = _error_summary(exc)

                    # If stream already started, finalize cleanly without switching model.
                    if chunk_count > 0:
                        yield "meta", _build_meta(
                            start=start,
                            attempted_models=attempted_models,
                            attempt_count=attempt_count,
                            final_source="bedrock",
                            final_model=model_id,
                            fallback_used=False,
                            last_error=last_error,
                            stream_interrupted=True,
                        )
                        return

                    # 🔴 BUG: same raise issue - fix to continue
                    continue  # ✅ Always try next model

        if source == "local":
            attempt_count += 1
            chunk_count = 0
            local_model = settings.mentor_local_chat_fallback_mode
            try:
                for chunk in engine.stream_chat_fallback(question, code_context):
                    chunk_count += 1
                    yield "chunk", {"text": chunk}

                if chunk_count == 0:
                    fallback_text = engine.generate_chat_fallback(question, code_context)
                    if fallback_text:
                        chunk_count += 1
                        yield "chunk", {"text": fallback_text}

                if chunk_count > 0:
                    yield "meta", _build_meta(
                        start=start,
                        attempted_models=attempted_models,
                        attempt_count=attempt_count,
                        final_source="local",
                        final_model=local_model,
                        fallback_used=bool(attempted_models),
                        last_error=last_error,
                    )
                    return

                last_error = {
                    "class": "EmptyResponse",
                    "category": "local_error",
                    "message": "Local stream fallback returned empty response",
                }

            except Exception as exc:
                last_error = {
                    "class": exc.__class__.__name__,
                    "category": "local_error",
                    "message": str(exc),
                }

    # If we get here, ALL routes failed (including local)
    # The duplicate fallback below is removed - local is handled in the loop above
    raise ModelRouterError("All mentor stream routes failed")
