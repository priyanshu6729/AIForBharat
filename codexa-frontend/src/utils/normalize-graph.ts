import type { GraphPayload, GraphNode, GraphEdge } from "@/types/contracts";

function normalizeNodeType(value: unknown): GraphNode["type"] {
  const type = String(value || "unknown").toLowerCase();
  if (type.includes("function")) return "function";
  if (type.includes("class")) return "class";
  if (type.includes("loop")) return "loop";
  if (type.includes("condition") || type.includes("if")) return "condition";
  if (type.includes("depend") || type.includes("import")) return "dependency";
  if (type.includes("call")) return "call";
  return "unknown";
}

function normalizeEdgeType(value: unknown): GraphEdge["type"] {
  const type = String(value || "unknown").toLowerCase();
  if (type.includes("call")) return "calls";
  if (type.includes("import")) return "imports";
  if (type.includes("depend")) return "depends";
  if (type.includes("contain")) return "contains";
  if (type.includes("next")) return "next";
  return "unknown";
}

export function normalizeGraphPayload(input: unknown): GraphPayload {
  const graph = (input && typeof input === "object" && "graph" in (input as Record<string, unknown>)
    ? (input as { graph: unknown }).graph
    : input) as Record<string, unknown> | null;

  if (!graph || typeof graph !== "object") {
    return { nodes: [], edges: [] };
  }

  const nodesRaw = Array.isArray(graph.nodes) ? graph.nodes : [];
  const edgesRaw = Array.isArray(graph.edges) ? graph.edges : [];

  const nodes: GraphNode[] = nodesRaw.map((node, index) => {
    const item = node as Record<string, unknown>;
    return {
      id: String(item.id ?? `node-${index}`),
      label: String(item.label ?? item.name ?? `Node ${index + 1}`),
      type: normalizeNodeType(item.type),
      range: item.range as GraphNode["range"],
      metadata: item,
    };
  });

  const edges: GraphEdge[] = edgesRaw.map((edge, index) => {
    const item = edge as Record<string, unknown>;
    const source = String(item.source ?? item.from ?? "");
    const target = String(item.target ?? item.to ?? "");
    return {
      id: String(item.id ?? `${source}-${target}-${index}`),
      source,
      target,
      type: normalizeEdgeType(item.type),
      label: item.type ? String(item.type) : undefined,
    };
  });

  return { nodes, edges };
}
