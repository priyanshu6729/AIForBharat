from __future__ import annotations

from typing import Any


class Graph:
    def __init__(self):
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, Any]] = []

    def add_node(self, node_type: str, props: dict[str, Any]) -> int:
        node_id = len(self.nodes) + 1
        self.nodes.append({"id": node_id, "type": node_type, "props": props})
        return node_id

    def add_edge(self, edge_type: str, src_id: int, dst_id: int, props: dict[str, Any] | None = None):
        self.edges.append(
            {
                "type": edge_type,
                "src_id": src_id,
                "dst_id": dst_id,
                "props": props or {},
            }
        )


def build_call_graph(ir: dict[str, Any]) -> Graph:
    graph = Graph()
    file_node = graph.add_node("File", {"path": ir["file"]})
    function_nodes: dict[str, int] = {}
    functions_by_name: dict[str, list[int]] = {}
    for fn in ir.get("functions", []):
        node_id = graph.add_node(
            "Function",
            {"name": fn["name"], "full_name": fn.get("full_name", fn["name"]), "file": ir["file"]},
        )
        function_nodes[fn.get("full_name", fn["name"])] = node_id
        functions_by_name.setdefault(fn["name"], []).append(node_id)

    for call in ir.get("calls", []):
        call_name = call.get("name")
        caller_scope = call.get("scope") or ""
        caller_key = f"{caller_scope}" if caller_scope else ""
        caller_node = function_nodes.get(caller_key)
        if call_name and call_name in functions_by_name:
            if caller_node is None:
                for callee_id in functions_by_name[call_name]:
                    graph.add_edge("CALLS", file_node, callee_id)
            else:
                for callee_id in functions_by_name[call_name]:
                    graph.add_edge("CALLS", caller_node, callee_id)

    return graph


def build_dependency_graph(ir: dict[str, Any]) -> Graph:
    graph = Graph()
    file_node = graph.add_node("File", {"path": ir["file"]})
    for imp in ir.get("imports", []):
        mod = imp.get("module") or imp.get("name")
        dep_node = graph.add_node("Module", {"name": mod})
        graph.add_edge("IMPORTS", file_node, dep_node)
    return graph


def build_cfg(ir: dict[str, Any]) -> Graph:
    graph = Graph()
    file_node = graph.add_node("File", {"path": ir["file"]})
    prev = file_node
    for control in ir.get("control_structures", []):
        node = graph.add_node("ControlNode", {"type": control["type"], "line": control["start_line"]})
        graph.add_edge("FLOWS_TO", prev, node)
        prev = node
    return graph


def build_dfg(ir: dict[str, Any]) -> Graph:
    graph = Graph()
    var_nodes: dict[str, int] = {}
    for var in ir.get("variables", []):
        node_id = graph.add_node(
            "Variable",
            {"name": var["name"], "line": var["start_line"], "file": ir["file"]},
        )
        var_nodes[var["name"]] = node_id

    for call in ir.get("calls", []):
        name = call.get("name")
        if name and name in var_nodes:
            call_node = graph.add_node("Call", {"name": name, "line": call["start_line"]})
            graph.add_edge("DATA_DEPENDS_ON", call_node, var_nodes[name])
    return graph


def merge_graphs(graphs: list[Graph]) -> Graph:
    merged = Graph()
    for graph in graphs:
        id_map: dict[int, int] = {}
        for node in graph.nodes:
            new_id = merged.add_node(node["type"], node.get("props", {}))
            id_map[node["id"]] = new_id
        for edge in graph.edges:
            merged.add_edge(edge["type"], id_map[edge["src_id"]], id_map[edge["dst_id"]], edge.get("props"))
    return merged
