"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";

import type { GraphPayload } from "@/types/contracts";

export function D3AnimatedGraph({ graph }: { graph: GraphPayload }) {
  const ref = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();

    const width = ref.current.clientWidth || 640;
    const height = ref.current.clientHeight || 300;

    const g = svg.append("g");
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.4, 2.5]).on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

    svg.call(zoom);

    const edges = g
      .append("g")
      .selectAll("line")
      .data(graph.edges)
      .join("line")
      .attr("stroke", "#64748B")
      .attr("stroke-width", 1.2)
      .attr("stroke-opacity", 0.7);

    const nodes = g
      .append("g")
      .selectAll("circle")
      .data(graph.nodes)
      .join("circle")
      .attr("r", 10)
      .attr("fill", (node) => (node.type === "function" ? "#6366F1" : "#22C55E"));

    const labels = g
      .append("g")
      .selectAll("text")
      .data(graph.nodes)
      .join("text")
      .text((node) => node.label)
      .attr("fill", "#CBD5E1")
      .attr("font-size", 11)
      .attr("text-anchor", "middle")
      .attr("dy", -14);

    const sim = d3
      .forceSimulation(graph.nodes as d3.SimulationNodeDatum[])
      .force("charge", d3.forceManyBody().strength(-250))
      .force(
        "link",
        d3.forceLink(graph.edges as d3.SimulationLinkDatum<d3.SimulationNodeDatum>[]).id((d: any) => d.id)
      )
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(26));

    sim.on("tick", () => {
      edges
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      nodes.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
      labels.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
    });

    return () => {
      sim.stop();
    };
  }, [graph]);

  return <svg ref={ref} className="h-full w-full rounded-xl border border-border bg-[#0B1224]" />;
}
