from __future__ import annotations
from typing import Any
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_java as tsjava
import tree_sitter_cpp as tscpp
import tree_sitter_c as tsc
from tree_sitter import Language, Parser
import re
from app.services.ast_parser_fallback import parse_python_details

PYTHON_TYPES = {
    "function_definition": "function",
    "for_statement": "loop",
    "while_statement": "loop",
    "if_statement": "condition",
    "import_statement": "dependency",
    "import_from_statement": "dependency",
    "call": "call",
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
    "call_expression": "call",
}

def get_parser(language: str):
    """Get tree-sitter parser for a given language."""
    parser = Parser()
    def _build_language(language_obj):
        try:
            return Language(language_obj)
        except Exception:
            return language_obj

    def _apply_language(language_obj):
        language_obj = _build_language(language_obj)
        if hasattr(parser, "set_language"):
            parser.set_language(language_obj)
        else:
            # Newer tree_sitter uses a writable language attribute instead of set_language
            parser.language = language_obj

    try:
        if language.lower() == 'python':
            _apply_language(tspython.language())
        elif language.lower() in ['javascript', 'typescript']:
            _apply_language(tsjavascript.language())
        elif language.lower() == 'java':
            _apply_language(tsjava.language())
        elif language.lower() in ['cpp', 'c++']:
            _apply_language(tscpp.language())
        elif language.lower() == 'c':
            _apply_language(tsc.language())
        else:
            raise ValueError(f"Unsupported language: {language}")
        
        return parser
    except Exception as e:
        raise ValueError(f"Failed to initialize parser for {language}: {str(e)}")

def parse_code(code: str, language: str):
    """Parse code and return IR-friendly AST details."""
    try:
        return parse_code_details(code, language)
    except Exception:
        if language.lower() == "python":
            return parse_python_details(code)
        return _parse_js_fallback(code)


def _parse_js_fallback(code: str) -> dict[str, Any]:
    """Lightweight JS fallback parser when tree-sitter is unavailable."""
    lines = code.splitlines()
    result = {"functions": [], "loops": [], "conditions": [], "dependencies": [], "calls": []}
    func_re = re.compile(r"\bfunction\s+([A-Za-z0-9_]+)")
    import_re = re.compile(r"^\s*import\s+")
    call_re = re.compile(r"\b([A-Za-z0-9_]+)\s*\(")

    for idx, line in enumerate(lines):
        if import_re.search(line):
            result["dependencies"].append(
                {"type": "dependency", "text": line.strip(), "range": [[idx, 0], [idx, 0]]}
            )
        func_match = func_re.search(line)
        if func_match:
            result["functions"].append(
                {"type": "function", "name": func_match.group(1), "range": [[idx, 0], [idx, 0]]}
            )
        if re.search(r"\bfor\s*\(", line) or re.search(r"\bwhile\s*\(", line) or re.search(r"\bdo\s*\{", line):
            result["loops"].append({"type": "loop", "range": [[idx, 0], [idx, 0]]})
        if re.search(r"\bif\s*\(", line):
            result["conditions"].append({"type": "condition", "range": [[idx, 0], [idx, 0]]})

        # Naive call detection (skip function declarations)
        if not func_match:
            call_match = call_re.search(line)
            if call_match:
                result["calls"].append(
                    {"type": "call", "name": call_match.group(1), "range": [[idx, 0], [idx, 0]]}
                )

    return result

def tree_to_dict(node):
    """Convert tree-sitter node to dictionary."""
    result = {
        "type": node.type,
        "start_point": list(node.start_point),
        "end_point": list(node.end_point),
    }
    
    if node.children:
        result["children"] = [tree_to_dict(child) for child in node.children]
    
    return result

def _node_text(code_bytes: bytes, node) -> str:
    return code_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")

def _extract_name(code_bytes: bytes, node) -> str | None:
    name_node = node.child_by_field_name("name") or node.child_by_field_name("property")
    if name_node:
        return _node_text(code_bytes, name_node).strip()
    return None

def _extract_call_name(code_bytes: bytes, node) -> str | None:
    # Python: call -> function field
    # JS: call_expression -> function field or callee
    fn_node = node.child_by_field_name("function") or node.child_by_field_name("callee")
    if fn_node:
        return _node_text(code_bytes, fn_node).strip()
    return None

def _walk(node, visitor):
    visitor(node)
    for child in node.children:
        _walk(child, visitor)

def parse_code_details(code: str, language: str) -> dict[str, Any]:
    """Parse code and extract detailed information about functions, loops, etc."""
    language = language.lower()
    if language not in {"python", "javascript"}:
        raise ValueError("Unsupported language")
    
    try:
        parser = get_parser(language)
        code_bytes = code.encode("utf-8")
        tree = parser.parse(code_bytes)
        root = tree.root_node
        
        result = {"functions": [], "loops": [], "conditions": [], "dependencies": [], "calls": []}
        type_map = PYTHON_TYPES if language == "python" else JS_TYPES
        key_map = {
            "function": "functions",
            "loop": "loops",
            "condition": "conditions",
            "dependency": "dependencies",
            "call": "calls",
        }
        
        def visitor(node):
            node_type = node.type
            if node_type in type_map:
                mapped = type_map[node_type]
                entry = {
                    "type": mapped,
                    "range": [list(node.start_point), list(node.end_point)],
                }
                if mapped == "call":
                    name = _extract_call_name(code_bytes, node)
                else:
                    name = _extract_name(code_bytes, node)
                if name:
                    entry["name"] = name
                if mapped == "dependency":
                    entry["text"] = _node_text(code_bytes, node).strip()

                result_key = key_map[mapped]
                result[result_key].append(entry)
        
        _walk(root, visitor)
        return result
    except Exception:
        if language == "python":
            return parse_python_details(code)
        return _parse_js_fallback(code)
