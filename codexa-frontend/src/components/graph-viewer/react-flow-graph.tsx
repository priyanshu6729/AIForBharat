"use client";

import { useMemo } from "react";

import type { CodeRange, GraphPayload } from "@/types/contracts";

type PositionedNode = {
  id: string;
  label: string;
  type: string;
  range?: CodeRange;
  x: number;
  y: number;
};

const NODE_W = 210;
const NODE_H = 58;
const X_GAP = 130;
const Y_GAP = 34;

function layoutGraph(graph: GraphPayload): PositionedNode[] {
  if (graph.nodes.length === 0) return [];

  const indegree = new Map<string, number>();
  const outgoing = new Map<string, string[]>();

  graph.nodes.forEach((node) => {
    indegree.set(node.id, 0);
    outgoing.set(node.id, []);
  });

  graph.edges.forEach((edge) => {
    indegree.set(edge.target, (indegree.get(edge.target) || 0) + 1);
    outgoing.set(edge.source, [...(outgoing.get(edge.source) || []), edge.target]);
  });

  const queue = graph.nodes.filter((node) => (indegree.get(node.id) || 0) === 0).map((node) => node.id);
  if (queue.length === 0) {
    queue.push(...graph.nodes.map((node) => node.id));
  }

  const rank = new Map<string, number>();
  queue.forEach((id) => rank.set(id, 0));

  while (queue.length) {
    const current = queue.shift()!;
    const currentRank = rank.get(current) || 0;
    (outgoing.get(current) || []).forEach((next) => {
      const nextRank = Math.max(rank.get(next) || 0, currentRank + 1);
      rank.set(next, nextRank);
      indegree.set(next, (indegree.get(next) || 1) - 1);
      if ((indegree.get(next) || 0) <= 0) {
        queue.push(next);
      }
    });
  }

  const groups = new Map<number, typeof graph.nodes>();
  graph.nodes.forEach((node) => {
    const nodeRank = rank.get(node.id) || 0;
    groups.set(nodeRank, [...(groups.get(nodeRank) || []), node]);
  });

  const positioned: PositionedNode[] = [];
  [...groups.entries()].forEach(([layer, nodes]) => {
    nodes.forEach((node, index) => {
      positioned.push({
        id: node.id,
        label: node.label,
        type: node.type,
        range: node.range,
        x: layer * (NODE_W + X_GAP),
        y: index * (NODE_H + Y_GAP),
      });
    });
  });

  return positioned;
}

function nodeColor(type: string) {
  switch (type) {
    case "function":
      return "#4F46E5";
    case "class":
      return "#14B8A6";
    case "loop":
      return "#F59E0B";
    case "condition":
      return "#22C55E";
    default:
      return "#64748B";
  }
}

export function ReactFlowGraph({
  graph,
  onSelectRange,
}: {
  graph: GraphPayload;
  onSelectRange?: (range?: CodeRange) => void;
}) {
  const nodes = useMemo(() => layoutGraph(graph), [graph]);
  const nodeLookup = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);

  const canvasWidth = Math.max(...nodes.map((node) => node.x), 0) + NODE_W + 160;
  const canvasHeight = Math.max(...nodes.map((node) => node.y), 0) + NODE_H + 120;

  return (
    <div className="h-full overflow-auto rounded-xl border border-border bg-[#0B1224] p-4">
      <div className="relative" style={{ width: canvasWidth, height: canvasHeight }}>
        <svg className="absolute left-0 top-0 h-full w-full pointer-events-none">
          {graph.edges.map((edge) => {
            const source = nodeLookup.get(edge.source);
            const target = nodeLookup.get(edge.target);
            if (!source || !target) return null;

            const x1 = source.x + NODE_W;
            const y1 = source.y + NODE_H / 2;
            const x2 = target.x;
            const y2 = target.y + NODE_H / 2;
            const midX = (x1 + x2) / 2;
            const path = `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;

            return (
              <g key={edge.id}>
                <path d={path} stroke="#64748B" strokeWidth="1.2" fill="none" />
                {edge.label ? (
                  <text x={midX} y={(y1 + y2) / 2 - 4} fill="#94A3B8" fontSize="10" textAnchor="middle">
                    {edge.label}
                  </text>
                ) : null}
              </g>
            );
          })}
        </svg>

        {nodes.map((node) => (
          <button
            key={node.id}
            onClick={() => onSelectRange?.(node.range)}
            className="absolute rounded-lg border border-border bg-[#101A30] px-3 py-2 text-left shadow-panel transition hover:border-primary/60"
            style={{ left: node.x, top: node.y, width: NODE_W, height: NODE_H }}
            title="Click to highlight code section"
          >
            <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: nodeColor(node.type) }}>
              {node.type}
            </p>
            <p className="truncate text-xs text-text">{node.label}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
