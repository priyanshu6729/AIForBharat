from __future__ import annotations

from typing import Any, Iterable, List, Tuple

Point = Tuple[int, int]
Range = Tuple[Point, Point]


def _normalize_range(raw_range: Any) -> Range | None:
    if not raw_range or len(raw_range) < 2:
        return None
    # Already in [[row, col], [row, col]] format
    if isinstance(raw_range[0], (list, tuple)) and isinstance(raw_range[1], (list, tuple)):
        if len(raw_range[0]) >= 2 and len(raw_range[1]) >= 2:
            return ((int(raw_range[0][0]), int(raw_range[0][1])), (int(raw_range[1][0]), int(raw_range[1][1])))
    # Fallback for [start, end] line-only ranges
    if isinstance(raw_range[0], int) and isinstance(raw_range[1], int):
        return ((int(raw_range[0]), 0), (int(raw_range[1]), 0))
    return None


def _range_contains(outer: list, inner: list) -> bool:
    outer_range = _normalize_range(outer)
    inner_range = _normalize_range(inner)
    if not outer_range or not inner_range:
        return False
    (osr, osc), (oer, oec) = outer_range
    (isr, isc), (ier, iec) = inner_range
    if (isr < osr) or (ier > oer):
        return False
    if isr == osr and isc < osc:
        return False
    if ier == oer and iec > oec:
        return False
    return True


def _make_id(prefix: str, item: dict, index: int) -> str:
    name = (item.get("name") or item.get("text") or "").replace(" ", "_")
    range_val = item.get("range") or []
    normalized = _normalize_range(range_val)
    start = normalized[0][0] if normalized else index
    return f"{prefix}:{name or index}:{start}"


def _find_container(item: dict, candidates: Iterable[dict]) -> dict | None:
    for candidate in candidates:
        if _range_contains(candidate.get("range"), item.get("range")):
            return candidate
    return None


def build_graph(ast: dict[str, Any]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    root_id = "root"
    nodes.append({"id": root_id, "label": "module", "type": "root"})

    functions = ast.get("functions", [])
    loops = ast.get("loops", [])
    conditions = ast.get("conditions", [])
    dependencies = ast.get("dependencies", [])
    calls = ast.get("calls", [])

    func_nodes = {}
    for idx, fn in enumerate(functions):
        node_id = _make_id("func", fn, idx)
        func_nodes[fn.get("name") or node_id] = node_id
        nodes.append({"id": node_id, "label": fn.get("name") or "function", "type": "function", "range": fn.get("range")})
        edges.append({"source": root_id, "target": node_id, "type": "contains"})

    for idx, dep in enumerate(dependencies):
        node_id = _make_id("dep", dep, idx)
        nodes.append({"id": node_id, "label": dep.get("name") or dep.get("text") or "dependency", "type": "dependency"})
        edges.append({"source": root_id, "target": node_id, "type": "imports"})

    def attach_control(items: list[dict], node_type: str):
        for idx, item in enumerate(items):
            node_id = _make_id(node_type, item, idx)
            nodes.append({"id": node_id, "label": item.get("name") or node_type, "type": node_type, "range": item.get("range")})
            container = _find_container(item, functions)
            if container:
                container_id = _make_id("func", container, 0)
                edges.append({"source": container_id, "target": node_id, "type": "contains"})
            else:
                edges.append({"source": root_id, "target": node_id, "type": "contains"})

    attach_control(loops, "loop")
    attach_control(conditions, "condition")

    for idx, call in enumerate(calls):
        node_id = _make_id("call", call, idx)
        call_label = call.get("name") or "call"
        nodes.append({"id": node_id, "label": call_label, "type": "call", "range": call.get("range")})

        container = _find_container(call, functions)
        container_id = root_id
        if container:
            container_id = _make_id("func", container, 0)
        edges.append({"source": container_id, "target": node_id, "type": "calls"})

        if call_label in func_nodes:
            edges.append({"source": container_id, "target": func_nodes[call_label], "type": "calls"})

    return {"nodes": nodes, "edges": edges}
