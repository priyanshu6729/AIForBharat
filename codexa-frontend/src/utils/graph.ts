import type { AnalyzeResponse, GraphEdge, GraphNode, GraphPayload } from "@/types/contracts";

function normalizeNodeType(kind?: string): GraphNode["type"] {
  const value = (kind || "unknown").toLowerCase();
  if (value.includes("function")) return "function";
  if (value.includes("class")) return "class";
  if (value.includes("loop")) return "loop";
  if (value.includes("condition") || value.includes("if")) return "condition";
  if (value.includes("import") || value.includes("dependency")) return "dependency";
  if (value.includes("call")) return "call";
  return "unknown";
}

function toNodeId(prefix: string, index: number, name?: string) {
  const safeName = (name || `${prefix}-${index}`).replace(/\s+/g, "-").toLowerCase();
  return `${prefix}-${safeName}-${index}`;
}

export function astToGraph(analysis: AnalyzeResponse | null): GraphPayload {
  if (!analysis?.ast) return { nodes: [], edges: [] };

  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const rootId = "root-module";

  nodes.push({ id: rootId, label: "Module", type: "unknown" });

  const groups: Array<[string, unknown[] | undefined, GraphNode["type"]]> = [
    ["fn", analysis.ast.functions, "function"],
    ["loop", analysis.ast.loops, "loop"],
    ["cond", analysis.ast.conditions, "condition"],
    ["dep", analysis.ast.dependencies, "dependency"],
    ["call", analysis.ast.calls, "call"],
  ];

  groups.forEach(([prefix, list, fallbackType]) => {
    (list || []).forEach((raw, index) => {
      const item = raw as Record<string, unknown>;
      const label = String(item.name || item.label || `${fallbackType}-${index + 1}`);
      const nodeId = toNodeId(prefix, index, label);
      nodes.push({
        id: nodeId,
        label,
        type: normalizeNodeType(String(item.type || fallbackType)),
        range: item.range as GraphNode["range"],
        metadata: item,
      });
      edges.push({
        id: `${rootId}-${nodeId}`,
        source: rootId,
        target: nodeId,
        type: "contains",
        label: "contains",
      });
    });
  });

  const functionNodes = nodes.filter((node) => node.type === "function");
  const callNodes = nodes.filter((node) => node.type === "call");

  callNodes.forEach((callNode, index) => {
    const target = functionNodes[index % Math.max(functionNodes.length, 1)]?.id;
    if (!target) return;
    edges.push({
      id: `call-${callNode.id}-${target}`,
      source: callNode.id,
      target,
      type: "calls",
      label: "calls",
    });
  });

  return { nodes, edges };
}
