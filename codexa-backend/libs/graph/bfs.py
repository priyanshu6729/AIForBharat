from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def bfs_graph_context(session: Session, project_id: int, node_ids: list[int], depth: int = 2) -> list[dict[str, Any]]:
    if not node_ids:
        return []
    visited = set(node_ids)
    frontier = set(node_ids)
    edges: list[dict[str, Any]] = []

    for _ in range(depth):
        if not frontier:
            break
        sql = text(
            """
            SELECT id, type, src_id, dst_id
            FROM graph_edges
            WHERE project_id = :project_id AND (src_id = ANY(:frontier) OR dst_id = ANY(:frontier))
            """
        )
        rows = session.execute(sql, {"project_id": project_id, "frontier": list(frontier)}).fetchall()
        next_frontier = set()
        for row in rows:
            edges.append(dict(row._mapping))
            src_id = row._mapping["src_id"]
            dst_id = row._mapping["dst_id"]
            if src_id not in visited:
                visited.add(src_id)
                next_frontier.add(src_id)
            if dst_id not in visited:
                visited.add(dst_id)
                next_frontier.add(dst_id)
        frontier = next_frontier
    return edges
