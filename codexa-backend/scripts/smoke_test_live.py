import json
import os
import sys
import requests

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
TOKEN = os.environ.get("TOKEN")


def request(method, path, **kwargs):
    url = f"{BASE_URL}{path}"
    resp = requests.request(method, url, timeout=10, **kwargs)
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    return resp.status_code, data


def main():
    print("== Codexa Backend Smoke Test ==")
    print("BASE_URL:", BASE_URL)

    status, data = request("GET", "/health")
    print("/health", status, data)
    if status != 200:
        print("Health check failed. Aborting.")
        sys.exit(1)

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

    status, session = request(
        "POST",
        "/api/session/save",
        json={
            "title": "Smoke Test",
            "language": "python",
            "code": code,
            "visualization": {"graph": viz.get("graph", {})},
            "chat_log": [{"question": "How do I solve this?", "response": guidance.get("response", "")}] ,
        },
        headers=headers,
    )
    print("/api/session/save", status)
    if status != 200:
        print("Session save failed:", session)
        sys.exit(1)

    session_id = session.get("session_id") if isinstance(session, dict) else None
    if not session_id:
        print("No session_id returned.")
        sys.exit(1)

    status, loaded = request("GET", f"/api/session/{session_id}", headers=headers)
    print("/api/session/{id}", status)
    if status != 200:
        print("Session load failed:", loaded)
        sys.exit(1)

    print("Smoke test completed successfully.")


if __name__ == "__main__":
    main()
