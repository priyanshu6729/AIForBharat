from __future__ import annotations


def classify_intent(question: str) -> str:
    lowered = question.lower()
    if "why" in lowered or "explain" in lowered:
        return "explain"
    if "debug" in lowered or "error" in lowered or "fail" in lowered:
        return "debug"
    if "teach" in lowered or "learn" in lowered:
        return "teach"
    if "refactor" in lowered or "improve" in lowered:
        return "refactor"
    return "general"
