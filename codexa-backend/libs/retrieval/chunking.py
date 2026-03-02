from __future__ import annotations

import hashlib
from typing import Iterable


def chunk_code(file_path: str, code: str, max_lines: int = 200) -> list[dict[str, str | int]]:
    lines = code.splitlines()
    chunks: list[dict[str, str | int]] = []
    start = 0
    while start < len(lines):
        end = min(start + max_lines, len(lines))
        content = "\n".join(lines[start:end])
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        chunks.append(
            {
                "file_path": file_path,
                "start_line": start + 1,
                "end_line": end,
                "content": content,
                "content_hash": content_hash,
            }
        )
        start = end
    return chunks
