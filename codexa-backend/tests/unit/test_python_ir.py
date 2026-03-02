from libs.parsing.python_ast import parse_python_ir


def test_parse_python_ir_extracts_functions():
    code = """
import os


def add(a, b):
    return a + b
"""
    ir = parse_python_ir("sample.py", code)
    assert ir.file == "sample.py"
    assert any(fn["name"] == "add" for fn in ir.functions)
    assert len(ir.imports) == 1
