from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def resolve_entities(session: Session, project_id: int, query: str, limit: int = 5) -> list[dict[str, Any]]:
    tokens = [token.strip() for token in query.replace("?", " ").split() if token.strip()]
    if not tokens:
        return []
    token = tokens[-1]
    sql = text(
        """
        SELECT id, type, name, file_path, start_line, end_line
        FROM code_entities
        WHERE project_id = :project_id AND name ILIKE :token
        LIMIT :limit
        """
    )
    rows = session.execute(sql, {"project_id": project_id, "token": f"%{token}%", "limit": limit}).fetchall()
    return [dict(row._mapping) for row in rows]
