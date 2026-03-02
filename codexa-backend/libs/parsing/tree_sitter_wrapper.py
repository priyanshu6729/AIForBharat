from __future__ import annotations

from typing import Any

try:
    from tree_sitter_languages import get_parser
except Exception:  # pragma: no cover
    get_parser = None


SUPPORTED_LANGS = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "go": "go",
}


def parse_with_tree_sitter(language: str, code: str) -> dict[str, Any]:
    if get_parser is None:
        raise RuntimeError("tree_sitter_languages not available")
    lang_key = SUPPORTED_LANGS.get(language)
    if not lang_key:
        raise ValueError(f"Unsupported language: {language}")
    parser = get_parser(lang_key)
    tree = parser.parse(bytes(code, "utf-8"))
    return {
        "root_type": tree.root_node.type,
        "root_start": tree.root_node.start_point,
        "root_end": tree.root_node.end_point,
    }
