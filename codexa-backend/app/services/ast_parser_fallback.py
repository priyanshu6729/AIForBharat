from __future__ import annotations
import ast
from typing import Any

def parse_python_code(code: str) -> dict:
    """Parse Python code using built-in ast module."""
    try:
        tree = ast.parse(code)
        return ast_to_dict(tree)
    except SyntaxError as e:
        raise ValueError(f"Syntax error: {str(e)}")

def ast_to_dict(node) -> dict:
    """Convert Python AST node to dictionary."""
    if isinstance(node, ast.AST):
        result = {"type": node.__class__.__name__}
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                result[field] = [ast_to_dict(item) for item in value]
            elif isinstance(value, ast.AST):
                result[field] = ast_to_dict(value)
            else:
                result[field] = value
        return result
    return node

def parse_python_details(code: str) -> dict[str, Any]:
    """Extract functions, loops, conditions from Python code."""
    try:
        tree = ast.parse(code)
        
        result = {
            "functions": [],
            "loops": [],
            "conditions": [],
            "dependencies": [],
            "calls": [],
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                line = node.lineno - 1 if hasattr(node, "lineno") else 0
                result["functions"].append({
                    "type": "function",
                    "name": node.name,
                    "line": node.lineno,
                    "range": [[line, 0], [line, 0]]
                })
            elif isinstance(node, (ast.For, ast.While)):
                line = node.lineno - 1 if hasattr(node, "lineno") else 0
                result["loops"].append({
                    "type": "loop",
                    "kind": node.__class__.__name__.lower(),
                    "line": node.lineno,
                    "range": [[line, 0], [line, 0]]
                })
            elif isinstance(node, ast.If):
                line = node.lineno - 1 if hasattr(node, "lineno") else 0
                result["conditions"].append({
                    "type": "condition",
                    "line": node.lineno,
                    "range": [[line, 0], [line, 0]]
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    line = node.lineno - 1 if hasattr(node, "lineno") else 0
                    result["dependencies"].append({
                        "type": "dependency",
                        "name": alias.name,
                        "line": node.lineno,
                        "range": [[line, 0], [line, 0]]
                    })
            elif isinstance(node, ast.Call):
                name = None
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                line = getattr(node, "lineno", 0)
                range_line = line - 1 if line else 0
                result["calls"].append({
                    "type": "call",
                    "name": name or "call",
                    "line": line,
                    "range": [[range_line, 0], [range_line, 0]]
                })
        
        return result
    except Exception as e:
        raise ValueError(f"Failed to parse Python code: {str(e)}")
