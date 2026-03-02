from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def search_similar_chunks(
    session: Session,
    project_id: int,
    query_vector: list[float],
    limit: int = 5,
) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT c.id, c.artifact_id, c.file_path, c.start_line, c.end_line, e.vector <-> :vec AS distance
        FROM embeddings e
        JOIN chunks c ON c.id = e.chunk_id
        WHERE e.project_id = :project_id
        ORDER BY e.vector <-> :vec
        LIMIT :limit
        """
    )
    rows = session.execute(sql, {"vec": query_vector, "project_id": project_id, "limit": limit}).fetchall()
    return [dict(row._mapping) for row in rows]


def search_text_chunks(session: Session, project_id: int, term: str, limit: int = 5) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT c.id, c.artifact_id, c.file_path, c.start_line, c.end_line
        FROM chunks c
        JOIN embeddings e ON e.chunk_id = c.id
        WHERE e.project_id = :project_id AND c.file_path ILIKE :term
        LIMIT :limit
        """
    )
    rows = session.execute(sql, {"project_id": project_id, "term": f"%{term}%", "limit": limit}).fetchall()
    return [dict(row._mapping) for row in rows]
