"use client";

import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { D3AnimatedGraph } from "@/components/graph-viewer/d3-animated-graph";
import { ReactFlowGraph } from "@/components/graph-viewer/react-flow-graph";
import type { CodeRange, GraphPayload } from "@/types/contracts";

export function GraphViewerPanel({
  graph,
  onSelectRange,
}: {
  graph: GraphPayload | null;
  onSelectRange: (range?: CodeRange) => void;
}) {
  const [engine, setEngine] = useState<"flow" | "d3">("flow");

  return (
    <Card className="h-full min-h-0">
      <CardHeader className="flex flex-row items-center justify-between py-2">
        <CardTitle>Graph Visualization</CardTitle>
        <div className="flex items-center gap-2">
          <Button variant={engine === "flow" ? "primary" : "ghost"} className="h-8 px-3" onClick={() => setEngine("flow")}>
            React Flow
          </Button>
          <Button variant={engine === "d3" ? "primary" : "ghost"} className="h-8 px-3" onClick={() => setEngine("d3")}>
            D3 Animate
          </Button>
        </div>
      </CardHeader>
      <CardContent className="h-[calc(100%-44px)] min-h-0">
        {!graph || graph.nodes.length === 0 ? (
          <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-border text-xs text-muted">
            Analyze and visualize code to render AST and call graphs.
          </div>
        ) : engine === "flow" ? (
          <ReactFlowGraph graph={graph} onSelectRange={onSelectRange} />
        ) : (
          <D3AnimatedGraph graph={graph} />
        )}
      </CardContent>
    </Card>
  );
}
