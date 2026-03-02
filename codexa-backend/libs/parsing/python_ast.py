from __future__ import annotations

import ast
from typing import Any

from libs.parsing.ir import IRFile


class IRBuilder(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.ir = IRFile(file=file_path, language="python")
        self._current_scope = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        scope = ".".join(self._current_scope)
        full_name = f"{scope}.{node.name}" if scope else node.name
        self.ir.functions.append(
            {
                "name": node.name,
                "full_name": full_name,
                "start_line": getattr(node, "lineno", 0),
                "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                "args": [arg.arg for arg in node.args.args],
                "scope": scope,
            }
        )
        self._current_scope.append(node.name)
        self.generic_visit(node)
        self._current_scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.ir.classes.append(
            {
                "name": node.name,
                "start_line": getattr(node, "lineno", 0),
                "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                "bases": [getattr(base, "id", "") for base in node.bases],
            }
        )
        self._current_scope.append(node.name)
        self.generic_visit(node)
        self._current_scope.pop()

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.ir.imports.append(
                {
                    "module": alias.name,
                    "asname": alias.asname,
                    "start_line": getattr(node, "lineno", 0),
                    "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                }
            )

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            self.ir.imports.append(
                {
                    "module": node.module,
                    "name": alias.name,
                    "asname": alias.asname,
                    "start_line": getattr(node, "lineno", 0),
                    "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                }
            )

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.ir.variables.append(
                    {
                        "name": target.id,
                        "scope": ".".join(self._current_scope),
                        "start_line": getattr(node, "lineno", 0),
                        "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
                    }
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        scope = ".".join(self._current_scope)
        self.ir.calls.append(
            {
                "name": name or "<unknown>",
                "scope": scope,
                "start_line": getattr(node, "lineno", 0),
                "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
            }
        )
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        self.ir.control_structures.append(
            {
                "type": "if",
                "start_line": getattr(node, "lineno", 0),
                "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
            }
        )
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.ir.control_structures.append(
            {
                "type": "for",
                "start_line": getattr(node, "lineno", 0),
                "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
            }
        )
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.ir.control_structures.append(
            {
                "type": "while",
                "start_line": getattr(node, "lineno", 0),
                "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
            }
        )
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        self.ir.control_structures.append(
            {
                "type": "try",
                "start_line": getattr(node, "lineno", 0),
                "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
            }
        )
        self.generic_visit(node)


def parse_python_ir(file_path: str, code: str) -> IRFile:
    tree = ast.parse(code)
    builder = IRBuilder(file_path)
    builder.visit(tree)
    return builder.ir
