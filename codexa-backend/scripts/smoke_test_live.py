import json
import os
import sys

import requests

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
TOKEN = os.environ.get("TOKEN")
EXPECT_INVALID_PRIMARY_MODEL = os.environ.get("EXPECT_INVALID_PRIMARY_MODEL", "").lower() in {
    "1",
    "true",
    "yes",
}
INVALID_PRIMARY_MODEL_ID = os.environ.get("INVALID_PRIMARY_MODEL_ID")


def request(method, path, **kwargs):
    url = f"{BASE_URL}{path}"
    resp = requests.request(method, url, timeout=15, **kwargs)
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    return resp.status_code, data


def stream_request(path, *, json_payload, headers):
    url = f"{BASE_URL}{path}"
    events: list[str] = []

    with requests.post(url, json=json_payload, headers=headers, stream=True, timeout=30) as resp:
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data: "):
                events.append(line[len("data: ") :])

    return resp.status_code, events


def main():
    print("== Codexa Backend Smoke Test ==")
    print("BASE_URL:", BASE_URL)

    status, data = request("GET", "/health")
    print("/health", status, data)
    if status != 200:
        print("Health check failed. Aborting.")
        sys.exit(1)

    if EXPECT_INVALID_PRIMARY_MODEL:
        status, detailed = request("GET", "/health/detailed")
        print("/health/detailed", status)
        mentor_models = detailed.get("mentor_models", {}) if isinstance(detailed, dict) else {}
        print("mentor_models:", mentor_models)
        configured_models = mentor_models.get("bedrock_models") or []
        if INVALID_PRIMARY_MODEL_ID and configured_models:
            if configured_models[0] != INVALID_PRIMARY_MODEL_ID:
                print(
                    "Warning: INVALID_PRIMARY_MODEL_ID does not match first configured model:",
                    configured_models[0],
                )

    code = """
import os

def foo():
    for i in range(3):
        if i:
            print(i)
"""

    status, analyze = request(
        "POST",
        "/api/analyze",
        json={"code": code, "language": "python"},
    )
    print("/api/analyze", status)
    if status != 200:
        print("Analyze failed:", analyze)
        sys.exit(1)

    ast = analyze.get("ast") if isinstance(analyze, dict) else None
    if not ast:
        print("Analyze returned no AST; aborting.")
        sys.exit(1)

    if not TOKEN:
        print("TOKEN not set. Skipping authenticated endpoints.")
        return

    headers = {"Authorization": f"Bearer {TOKEN}"}

    status, viz = request("POST", "/api/visualize", json={"ast": ast}, headers=headers)
    print("/api/visualize", status)
    if status != 200:
        print("Visualize failed:", viz)
        sys.exit(1)

    status, guidance = request(
        "POST",
        "/api/guidance",
        json={
            "user_question": "How do I solve this?",
            "code_context": code,
            "ast_context": ast,
            "guidance_level": 1,
        },
        headers=headers,
    )
    print("/api/guidance", status)
    if status != 200:
        print("Guidance failed:", guidance)
        sys.exit(1)

    session_id = guidance.get("session_id") if isinstance(guidance, dict) else None

    status, chat = request(
        "POST",
        "/api/chat",
        json={
            "user_question": "Explain what this function is doing.",
            "code_context": code,
            "ast_context": ast,
            "session_id": session_id,
        },
        headers=headers,
    )
    print("/api/chat", status)
    if status != 200:
        print("Chat failed:", chat)
        sys.exit(1)

    status, events = stream_request(
        "/api/chat/stream",
        json_payload={
            "user_question": "Continue with one optimization tip.",
            "code_context": code,
            "ast_context": ast,
            "session_id": session_id,
        },
        headers=headers,
    )
    print("/api/chat/stream", status)
    if status != 200:
        print("Streaming chat failed with status:", status)
        sys.exit(1)

    done_seen = False
    stream_text_parts: list[str] = []
    for raw in events:
        try:
            event = json.loads(raw)
        except Exception:
            continue
        if event.get("text"):
            stream_text_parts.append(event["text"])
        if event.get("done") is True:
            done_seen = True

    if not done_seen:
        print("Streaming chat did not emit terminal done event.")
        sys.exit(1)

    if not "".join(stream_text_parts).strip():
        print("Streaming chat returned no text chunks.")
        sys.exit(1)

    status, saved = request(
        "POST",
        "/api/session/save",
        json={
            "title": "Smoke Test",
            "language": "python",
            "code": code,
            "visualization": {"graph": viz.get("graph", {})},
            "chat_log": [
                {
                    "question": "How do I solve this?",
                    "response": guidance.get("response", ""),
                }
            ],
        },
        headers=headers,
    )
    print("/api/session/save", status)
    if status != 200:
        print("Session save failed:", saved)
        sys.exit(1)

    saved_session_id = saved.get("session_id") if isinstance(saved, dict) else None
    if not saved_session_id:
        print("No session_id returned.")
        sys.exit(1)

    status, loaded = request("GET", f"/api/session/{saved_session_id}", headers=headers)
    print("/api/session/{id}", status)
    if status != 200:
        print("Session load failed:", loaded)
        sys.exit(1)

    if EXPECT_INVALID_PRIMARY_MODEL:
        print("Fallback smoke mode enabled: mentor endpoints stayed healthy with invalid primary model config.")

    print("Smoke test completed successfully.")


if __name__ == "__main__":
    main()
