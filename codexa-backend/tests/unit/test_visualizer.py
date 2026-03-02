from app.services.visualizer import build_graph


def test_build_graph():
    ast = {
        "functions": [{"name": "foo", "range": [0, 1]}],
        "loops": [{"type": "loop", "range": [2, 3]}],
        "conditions": [],
        "dependencies": [{"text": "import os", "range": [0, 0]}],
    }
    graph = build_graph(ast)
    assert graph["nodes"]
    assert graph["edges"]
