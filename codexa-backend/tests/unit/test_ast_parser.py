from app.services.ast_parser import parse_code


def test_parse_python_ast():
    code = """
import os

def foo():
    for i in range(3):
        if i:
            print(i)
"""
    result = parse_code(code, "python")
    assert result["functions"]
    assert result["loops"]
    assert result["conditions"]
    assert result["dependencies"]


def test_parse_js_ast():
    code = """
import x from 'y';
function bar() {
  for (let i = 0; i < 3; i++) {
    if (i) console.log(i);
  }
}
"""
    result = parse_code(code, "javascript")
    assert result["functions"]
    assert result["loops"]
    assert result["conditions"]
