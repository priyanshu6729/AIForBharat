from __future__ import annotations

import io
import zipfile
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from libs.common.aws import s3_get_bytes
from libs.common.config import settings
from libs.common.db import get_session
from libs.common.models import AnalysisJob, Artifact, Answer
from libs.graph.bfs import bfs_graph_context
from libs.retrieval.embeddings import embed_texts
from libs.retrieval.entity_linking import resolve_entities
from libs.retrieval.intent import classify_intent
from libs.retrieval.llm import generate_response
from libs.retrieval.search import search_similar_chunks

router = APIRouter()


class Request(BaseModel):
    question: str
    project_id: int
    mode: str | None = None
    learner_level: str | None = None


class Response(BaseModel):
    answer: str
    evidence: list[dict[str, Any]]
    teaching_steps: list[str]
    followups: list[str]


def _parse_s3_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("s3://"):
        raise ValueError("Invalid S3 uri")
    _, rest = uri.split("s3://", 1)
    bucket, key = rest.split("/", 1)
    return bucket, key


def _load_artifact_files(artifact: Artifact) -> dict[str, str]:
    bucket, key = _parse_s3_uri(artifact.s3_uri)
    payload = s3_get_bytes(bucket, key)
    if artifact.type == "zip":
        file_map: dict[str, str] = {}
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                content = archive.read(info).decode("utf-8", errors="ignore")
                file_map[info.filename] = content
        return file_map
    return {"snippet.py": payload.decode("utf-8", errors="ignore")}


def _extract_chunk_text(file_map: dict[str, str], file_path: str, start_line: int, end_line: int) -> str:
    content = file_map.get(file_path, "")
    if not content:
        return ""
    lines = content.splitlines()
    start = max(start_line - 1, 0)
    end = min(end_line, len(lines))
    return "\n".join(lines[start:end])


def _build_prompt(
    question: str,
    intent: str,
    mode: str,
    evidence: list[dict[str, Any]],
    graph_context: list[dict[str, Any]],
) -> str:
    evidence_block = "\n\n".join(
        [f"File: {item['file_path']}\nLines: {item['start_line']}-{item['end_line']}\n{item['content']}" for item in evidence]
    )
    graph_block = "\n".join(
        [f"{edge['type']}: {edge['src_id']} -> {edge['dst_id']}" for edge in graph_context[:20]]
    )
    if mode == "socratic":
        guidance = "Respond with guiding questions, not direct answers."
    elif mode == "hint":
        guidance = "Provide partial hints and ask the learner to finish."
    else:
        guidance = "Provide a clear explanation with step-by-step reasoning."

    return (
        f"You are Codexa, an AI pair programmer focused on learning.\n"
        f"Intent: {intent}\n"
        f"Teaching mode: {mode}\n"
        f"Guidance: {guidance}\n"
        f"Question: {question}\n"
        f"Relevant code:\n{evidence_block}\n"
        f"Graph context:\n{graph_block}\n"
        "Answer:" 
    )


@router.post("/", response_model=Response)
def query_code(payload: Request, session: Session = Depends(get_session)):
    mode = payload.mode or settings.default_teaching_mode
    intent = classify_intent(payload.question)

    _embedding = embed_texts([payload.question])[0]
    similar_chunks = search_similar_chunks(session, payload.project_id, _embedding, limit=5)
    if similar_chunks and similar_chunks[0].get("distance", 1.0) < 0.1:
        mode = "explanation"

    evidence: list[dict[str, Any]] = []
    artifact_cache: dict[int, dict[str, str]] = {}
    for chunk in similar_chunks:
        artifact_id = chunk["artifact_id"]
        if artifact_id not in artifact_cache:
            artifact = session.get(Artifact, artifact_id)
            if artifact is None:
                continue
            artifact_cache[artifact_id] = _load_artifact_files(artifact)
        file_map = artifact_cache.get(artifact_id, {})
        content = _extract_chunk_text(
            file_map,
            chunk["file_path"],
            chunk["start_line"],
            chunk["end_line"],
        )
        evidence.append(
            {
                "chunk_id": chunk["id"],
                "file_path": chunk["file_path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "content": content,
            }
        )

    entities = resolve_entities(session, payload.project_id, payload.question)
    entity_ids = [entity["id"] for entity in entities]
    graph_node_ids: list[int] = []
    if entity_ids:
        rows = session.execute(
            text(
                """
                SELECT id FROM graph_nodes
                WHERE project_id = :project_id AND entity_id = ANY(:entity_ids)
                """
            ),
            {"project_id": payload.project_id, "entity_ids": entity_ids},
        ).fetchall()
        graph_node_ids = [row[0] for row in rows]
    graph_context = bfs_graph_context(session, payload.project_id, graph_node_ids, depth=2)

    prompt = _build_prompt(payload.question, intent, mode, evidence, graph_context)
    answer = generate_response(prompt)

    from libs.common.models import Query
    
    db_query = Query(
        project_id=payload.project_id,
        user_id=None,
        question=payload.question,
        mode=mode,
    )
    session.add(db_query)
    session.commit()
    session.refresh(db_query)

    db_answer = Answer(
        query_id=db_query.id,
        response=answer,
        evidence_ids=[item["chunk_id"] for item in evidence],
    )
    session.add(db_answer)
    session.commit()

    teaching_steps = []
    if mode == "socratic":
        teaching_steps = ["Identify the relevant function.", "Trace the data flow.", "Predict the outcome before reading further."]
    elif mode == "hint":
        teaching_steps = ["Focus on the control flow around the condition.", "Explain the variable updates in your own words."]
    else:
        teaching_steps = ["Summarize the main purpose of the code.", "List the key steps in order."]

    followups = ["Do you want a deeper walk-through of a specific function?"]

    return Response(
        answer=answer,
        evidence=evidence,
        teaching_steps=teaching_steps,
        followups=followups,
    ) 