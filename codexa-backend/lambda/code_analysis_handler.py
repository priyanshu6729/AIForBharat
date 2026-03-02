from __future__ import annotations

import json
from tree_sitter_languages import get_parser


PYTHON_TYPES = {
    "function_definition": "function",
    "for_statement": "loop",
    "while_statement": "loop",
    "if_statement": "condition",
    "import_statement": "dependency",
    "import_from_statement": "dependency",
}

JS_TYPES = {
    "function_declaration": "function",
    "method_definition": "function",
    "arrow_function": "function",
    "for_statement": "loop",
    "while_statement": "loop",
    "do_statement": "loop",
    "if_statement": "condition",
    "import_statement": "dependency",
    "lexical_declaration": "dependency",
    "variable_declaration": "dependency",
}


def _node_text(code_bytes: bytes, node) -> str:
    return code_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")


def _extract_name(code_bytes: bytes, node) -> str | None:
    name_node = node.child_by_field_name("name")
    if name_node:
        return _node_text(code_bytes, name_node).strip()
    return None


def _walk(node, visitor):
    visitor(node)
    for child in node.children:
        _walk(child, visitor)


def parse_code(code: str, language: str) -> dict:
    language = language.lower()
    if language not in {"python", "javascript"}:
        raise ValueError("Unsupported language")

    parser = get_parser("python" if language == "python" else "javascript")
    code_bytes = code.encode("utf-8")
    tree = parser.parse(code_bytes)
    root = tree.root_node

    result = {"functions": [], "loops": [], "conditions": [], "dependencies": []}
    type_map = PYTHON_TYPES if language == "python" else JS_TYPES

    def visitor(node):
        node_type = node.type
        if node_type in type_map:
            entry = {
                "type": type_map[node_type],
                "range": [node.start_point, node.end_point],
            }
            name = _extract_name(code_bytes, node)
            if name:
                entry["name"] = name
            if type_map[node_type] == "dependency":
                entry["text"] = _node_text(code_bytes, node).strip()
            result_key = f"{type_map[node_type]}s"
            result[result_key].append(entry)

    _walk(root, visitor)
    return result


def handler(event, context):
    body = event
    if isinstance(event, dict) and "body" in event:
        body = json.loads(event["body"])
    code = body.get("code", "")
    language = body.get("language", "python")
    result = parse_code(code, language)
    return result
