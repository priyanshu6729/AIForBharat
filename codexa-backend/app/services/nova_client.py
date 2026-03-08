from __future__ import annotations

import json
import logging
from typing import Any, Generator

import boto3
from botocore.config import Config
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Codexa, an expert AI programming mentor and assistant. You:
- Answer programming questions clearly and thoroughly
- Remember and reference previous messages in the conversation
- Understand code context and explain it progressively
- Can explain concepts, debug code, suggest improvements
- Provide complete, working code examples when asked
- Adapt explanation depth based on the conversation flow
- Reference earlier parts of the conversation when relevant

When analyzing code:
- Explain what it does step by step
- Identify potential issues
- Suggest improvements
- Answer follow-up questions with full context awareness"""

SOCRATIC_SYSTEM_PROMPT = """You are Codexa, a Socratic programming tutor. You:
- Guide students to discover answers themselves
- Ask probing questions instead of giving direct answers
- Remember the full conversation context
- Build on previous hints given in this session
- Adjust guidance based on student's progress shown in conversation history

STRICT RULES:
- NEVER provide complete solutions
- Maximum 8 lines of code for level 4
- Always reference what was discussed before"""

_BEDROCK_RETRY_CONFIG = Config(
    retries={"max_attempts": 4, "mode": "adaptive"},
    connect_timeout=10,
    read_timeout=45,
)


def _bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.bedrock_region,
        config=_BEDROCK_RETRY_CONFIG,
    )


def normalize_bedrock_error(exc: Exception) -> dict[str, Any]:
    """Normalize Bedrock/provider exceptions for model-router decisions."""
    message = str(exc)
    category = "unknown"
    recoverable = False
    code: str | None = None

    if isinstance(exc, ClientError):
        error = exc.response.get("Error", {}) if isinstance(exc.response, dict) else {}
        code = error.get("Code") or None
        provider_message = error.get("Message")
        if provider_message:
            message = provider_message

        lowered = f"{(code or '').lower()} {message.lower()}"
        if "throttl" in lowered:
            category = "throttling"
            recoverable = True
        elif "accessdenied" in lowered or "not authorized" in lowered or "access denied" in lowered:
            category = "access_denied"
            recoverable = True
        elif "model" in lowered and (
            "notfound" in lowered or "not found" in lowered or "does not exist" in lowered
        ):
            category = "model_not_found"
            recoverable = True
        elif "timeout" in lowered or "temporar" in lowered or "unavailable" in lowered:
            category = "timeout_network"
            recoverable = True
        else:
            category = "provider_error"

    elif isinstance(exc, (EndpointConnectionError, ReadTimeoutError, ConnectTimeoutError, TimeoutError)):
        category = "timeout_network"
        recoverable = True
    elif isinstance(exc, BotoCoreError):
        category = "provider_error"
        recoverable = True

    return {
        "category": category,
        "recoverable": recoverable,
        "code": code,
        "message": message,
        "exception_class": exc.__class__.__name__,
    }


def _build_messages(
    question: str,
    conversation_history: list[dict] | None = None,
    system_context: str | None = None,
) -> list[dict]:
    """Build message history for Nova - enables multi-turn conversation."""
    messages: list[dict] = []

    if conversation_history:
        for entry in conversation_history[-8:]:
            question_text = entry.get("question", "")
            response_text = entry.get("response", "")
            if question_text:
                messages.append(
                    {
                        "role": "user",
                        "content": [{"text": question_text}],
                    }
                )
            if response_text:
                messages.append(
                    {
                        "role": "assistant",
                        "content": [{"text": response_text}],
                    }
                )

    current_text = question
    if system_context:
        current_text = f"{system_context}\n\nQuestion: {question}"

    messages.append(
        {
            "role": "user",
            "content": [{"text": current_text}],
        }
    )

    return messages


def _resolve_model_id(model_id: str | None) -> str:
    resolved = model_id or settings.nova_model_id
    if not resolved:
        raise RuntimeError("NOVA_MODEL_ID not configured")
    return resolved


def _invoke_nova(
    prompt: str,
    max_tokens: int = 500,
    conversation_history: list[dict] | None = None,
    system_prompt: str | None = None,
    model_id: str | None = None,
) -> str:
    """Invoke AWS Bedrock Nova with conversation history."""
    resolved_model_id = _resolve_model_id(model_id)

    try:
        client = _bedrock_client()
        messages = _build_messages(prompt, conversation_history)

        payload = {
            "schemaVersion": "messages-v1",
            "messages": messages,
            "system": [{"text": system_prompt or SYSTEM_PROMPT}],
            "inferenceConfig": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
            },
        }

        response = client.invoke_model(
            modelId=resolved_model_id,
            body=json.dumps(payload),
            accept="application/json",
            contentType="application/json",
        )

        body = json.loads(response["body"].read())
        if isinstance(body, dict) and "output" in body:
            output = body.get("output")
            if isinstance(output, dict):
                message = output.get("message")
                if isinstance(message, dict):
                    content = message.get("content", [])
                    if content and isinstance(content, list):
                        return content[0].get("text", "")

        logger.warning("Unexpected Nova response format for model %s: %s", resolved_model_id, body)
        return ""

    except Exception as exc:
        error = normalize_bedrock_error(exc)
        logger.error(
            "Bedrock invoke failed model=%s category=%s code=%s message=%s",
            resolved_model_id,
            error["category"],
            error["code"],
            error["message"],
        )
        raise


def _invoke_nova_stream(
    prompt: str,
    max_tokens: int = 500,
    conversation_history: list[dict] | None = None,
    system_prompt: str | None = None,
    model_id: str | None = None,
) -> Generator[str, None, None]:
    """Stream response from Nova - enables ChatGPT-like typing effect."""
    resolved_model_id = _resolve_model_id(model_id)

    try:
        client = _bedrock_client()
        messages = _build_messages(prompt, conversation_history)

        payload = {
            "schemaVersion": "messages-v1",
            "messages": messages,
            "system": [{"text": system_prompt or SYSTEM_PROMPT}],
            "inferenceConfig": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
            },
        }

        response = client.invoke_model_with_response_stream(
            modelId=resolved_model_id,
            body=json.dumps(payload),
            accept="application/json",
            contentType="application/json",
        )

        for event in response["body"]:
            chunk = event.get("chunk") if isinstance(event, dict) else None
            if not chunk:
                continue

            chunk_data = json.loads(chunk["bytes"].decode())
            delta = chunk_data.get("contentBlockDelta", {})
            text = delta.get("delta", {}).get("text", "")
            if text:
                yield text

    except Exception as exc:
        error = normalize_bedrock_error(exc)
        logger.error(
            "Bedrock stream failed model=%s category=%s code=%s message=%s",
            resolved_model_id,
            error["category"],
            error["code"],
            error["message"],
        )
        raise


def analyze_with_nova(
    code: str,
    language: str,
    ast: dict,
    conversation_history: list[dict] | None = None,
    model_id: str | None = None,
) -> dict | None:
    """Analyze code with context awareness."""
    try:
        prompt = (
            f"Analyze this {language} code:\n\n"
            f"```{language}\n{code}\n```\n\n"
            f"AST Structure: {json.dumps(ast, indent=2)}\n\n"
            "Provide:\n"
            "1. A clear summary of what the code does\n"
            "2. 3-4 guiding questions to deepen understanding\n"
            "3. Any potential issues or edge cases\n\n"
            "Respond in JSON: "
            '{"summary": "...", "hints": ["...", "..."], "issues": ["...", "..."]}'
        )

        response_text = _invoke_nova(
            prompt,
            max_tokens=600,
            conversation_history=conversation_history,
            system_prompt=SYSTEM_PROMPT,
            model_id=model_id,
        )

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "summary": response_text[:200] if response_text else "Analysis complete.",
                "hints": ["Review the code structure and flow"],
                "issues": [],
            }

    except Exception as exc:
        logger.warning("Nova analysis failed: %s", exc)
        return None


def guidance_with_nova(
    question: str,
    code: str,
    ast: dict,
    goal: str | None = None,
    guidance_level: int = 0,
    explicit_full: bool = False,
    conversation_history: list[dict] | None = None,
    model_id: str | None = None,
) -> str | None:
    """Provide context-aware Socratic guidance with conversation memory."""

    if guidance_level >= 5:
        guidance_level = 4

    goal_line = f"Learning goal: {goal}\n" if goal else ""

    level_instructions = {
        0: "Ask 1-2 clarifying questions about inputs, outputs, or constraints. Reference previous discussion if relevant.",
        1: "Provide a high-level conceptual hint (one sentence). Build on hints already given in this conversation.",
        2: "Give a 3-4 step outline. Reference what the student has already tried based on conversation history.",
        3: "Provide structured pseudocode. Acknowledge progress made in previous messages.",
        4: "Give a minimal code hint (max 8 lines) for ONE specific technique. Build on the conversation so far.",
    }

    instruction = level_instructions.get(guidance_level, level_instructions[1])

    history_note = ""
    if conversation_history and len(conversation_history) > 0:
        history_note = (
            f"\nThis is message #{len(conversation_history) + 1} in this session. "
            "Reference earlier context when relevant.\n"
        )

    prompt = (
        f"{goal_line}"
        f"Guidance level: {guidance_level} - {instruction}\n"
        f"{history_note}"
        f"Student question: {question}\n\n"
        f"Code context:\n```\n{code}\n```\n\n"
        f"AST info: {json.dumps(ast)}"
    )

    try:
        response = _invoke_nova(
            prompt,
            max_tokens=500,
            conversation_history=conversation_history,
            system_prompt=SOCRATIC_SYSTEM_PROMPT,
            model_id=model_id,
        )

        if len(response) > 800 or response.count("\n") > 15:
            lines = response.split("\n")[:10]
            response = "\n".join(lines) + "\n\n💡 Try implementing this and ask follow-up questions!"

        return response.strip()

    except Exception as exc:
        logger.warning("Nova guidance failed: %s", exc)
        return None


def chat_with_nova(
    question: str,
    code: str | None = None,
    conversation_history: list[dict] | None = None,
    model_id: str | None = None,
) -> str | None:
    """
    General chat - full ChatGPT-like responses with context memory.
    Use this for open-ended questions, explanations, debugging help.
    """
    context = ""
    if code:
        context = f"\n\nCurrent code context:\n```\n{code}\n```\n"

    prompt = f"{question}{context}"

    try:
        return _invoke_nova(
            prompt,
            max_tokens=1000,
            conversation_history=conversation_history,
            system_prompt=SYSTEM_PROMPT,
            model_id=model_id,
        )
    except Exception as exc:
        logger.warning("Nova chat failed: %s", exc)
        return None


def stream_chat_with_nova(
    question: str,
    code: str | None = None,
    conversation_history: list[dict] | None = None,
    model_id: str | None = None,
) -> Generator[str, None, None]:
    """
    Streaming chat - yields text chunks like ChatGPT typing effect.
    Use with FastAPI StreamingResponse.
    """
    context = ""
    if code:
        context = f"\n\nCurrent code context:\n```\n{code}\n```\n"

    prompt = f"{question}{context}"

    yield from _invoke_nova_stream(
        prompt,
        max_tokens=1000,
        conversation_history=conversation_history,
        system_prompt=SYSTEM_PROMPT,
        model_id=model_id,
    )
