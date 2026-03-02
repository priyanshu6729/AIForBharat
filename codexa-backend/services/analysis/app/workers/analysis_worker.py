from __future__ import annotations

import io
import json
import logging
import os
import shutil
import subprocess
import tempfile
import zipfile
from typing import Any

from sqlalchemy.orm import Session

from libs.common.aws import s3_get_bytes, s3_put_json
from libs.common.config import settings
from libs.common.models import (
    AnalysisJob,
    Artifact,
    Chunk,
    CodeEntity,
    Embedding,
    GraphEdge,
    GraphNode,
    GraphVersion,
    IrArtifact,
)
from libs.graph.builders import build_call_graph, build_cfg, build_dependency_graph, build_dfg, merge_graphs
from libs.parsing.ir import IRFile
from libs.parsing.python_ast import parse_python_ir
from libs.retrieval.chunking import chunk_code
from libs.retrieval.embeddings import embed_texts

logger = logging.getLogger(__name__)


EXT_LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
}


def _parse_s3_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("s3://"):
        raise ValueError("Invalid S3 uri")
    _, rest = uri.split("s3://", 1)
    bucket, key = rest.split("/", 1)
    return bucket, key


def _infer_language(file_path: str) -> str:
    _, ext = os.path.splitext(file_path)
    return EXT_LANG_MAP.get(ext.lower(), "unknown")


def _should_ingest(file_path: str) -> bool:
    _, ext = os.path.splitext(file_path)
    return ext.lower() in EXT_LANG_MAP


def _parse_file(file_path: str, code: str) -> IRFile:
    language = _infer_language(file_path)
    if language == "python":
        return parse_python_ir(file_path, code)
    return IRFile(file=file_path, language=language)


def _persist_entities(session: Session, project_id: int, ir: dict[str, Any]) -> list[CodeEntity]:
    entities: list[CodeEntity] = []
    for fn in ir.get("functions", []):
        entities.append(
            CodeEntity(
                project_id=project_id,
                type="function",
                name=fn["name"],
                file_path=ir["file"],
                start_line=fn.get("start_line", 0),
                end_line=fn.get("end_line", 0),
                props_json=fn,
            )
        )
    for cls in ir.get("classes", []):
        entities.append(
            CodeEntity(
                project_id=project_id,
                type="class",
                name=cls["name"],
                file_path=ir["file"],
                start_line=cls.get("start_line", 0),
                end_line=cls.get("end_line", 0),
                props_json=cls,
            )
        )
    for var in ir.get("variables", []):
        entities.append(
            CodeEntity(
                project_id=project_id,
                type="variable",
                name=var["name"],
                file_path=ir["file"],
                start_line=var.get("start_line", 0),
                end_line=var.get("end_line", 0),
                props_json=var,
            )
        )
    session.add_all(entities)
    session.commit()
    return entities


def _persist_graph(session: Session, project_id: int, graph_payload: dict[str, Any]) -> None:
    nodes = []
    node_id_map: dict[int, int] = {}
    for node in graph_payload.get("nodes", []):
        entity_id = None
        node_type = node["type"].lower()
        props = node.get("props", {})
        name = props.get("name")
        file_path = props.get("file")
        if name and node_type in {"function", "variable", "class"}:
            query = (
                session.query(CodeEntity)
                .filter(CodeEntity.project_id == project_id)
                .filter(CodeEntity.type == node_type)
                .filter(CodeEntity.name == name)
            )
            if file_path:
                query = query.filter(CodeEntity.file_path == file_path)
            entity = query.first()
            if entity:
                entity_id = entity.id
        db_node = GraphNode(
            project_id=project_id,
            type=node["type"],
            entity_id=entity_id,
            props_json=node.get("props", {}),
        )
        session.add(db_node)
        session.flush()
        node_id_map[node["id"]] = db_node.id
        nodes.append(db_node)

    edges = []
    for edge in graph_payload.get("edges", []):
        edges.append(
            GraphEdge(
                project_id=project_id,
                type=edge["type"],
                src_id=node_id_map[edge["src_id"]],
                dst_id=node_id_map[edge["dst_id"]],
                props_json=edge.get("props", {}),
            )
        )
    session.add_all(edges)
    session.commit()


def _persist_embeddings(session: Session, project_id: int, artifact_id: int, file_path: str, code: str):
    chunks = chunk_code(file_path, code)
    if not chunks:
        return
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        db_chunk = Chunk(
            artifact_id=artifact_id,
            file_path=chunk["file_path"],
            start_line=int(chunk["start_line"]),
            end_line=int(chunk["end_line"]),
            content_hash=str(chunk["content_hash"]),
        )
        session.add(db_chunk)
        session.flush()
        session.add(
            Embedding(
                project_id=project_id,
                chunk_id=db_chunk.id,
                vector=vector,
                model=settings.titan_embedding_model_id,
            )
        )
    session.commit()


def run_job(job_id: int, session: Session) -> None:
    job = session.get(AnalysisJob, job_id)
    if job is None:
        raise ValueError("Job not found")

    try:
        job.status = "running"
        job.stage = "parsing"
        session.commit()

        artifact = session.get(Artifact, job.artifact_id)
        if artifact is None:
            job.status = "failed"
            job.error = "artifact not found"
            session.commit()
            return

        bucket, key = _parse_s3_uri(artifact.s3_uri)
        payload = s3_get_bytes(bucket, key)

        file_map: dict[str, str] = {}
        if artifact.type == "repo_url":
            repo_url = payload.decode("utf-8", errors="ignore").strip()
            if not repo_url:
                job.status = "failed"
                job.error = "repo_url empty"
                session.commit()
                return
            temp_dir = tempfile.mkdtemp(prefix="codexa-repo-")
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, temp_dir],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                for root, _, files in os.walk(temp_dir):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        if not _should_ingest(file_path):
                            continue
                        rel_path = os.path.relpath(file_path, temp_dir)
                        with open(file_path, "rb") as handle:
                            content = handle.read().decode("utf-8", errors="ignore")
                        file_map[rel_path] = content
            except subprocess.CalledProcessError as exc:
                job.status = "failed"
                job.error = f"git clone failed: {exc.stderr.decode('utf-8', errors='ignore')}"
                session.commit()
                return
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        elif artifact.type == "zip":
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    if not _should_ingest(info.filename):
                        continue
                    content = archive.read(info).decode("utf-8", errors="ignore")
                    file_map[info.filename] = content
        else:
            file_map["snippet.py"] = payload.decode("utf-8", errors="ignore")

        if not file_map:
            job.status = "failed"
            job.error = "no supported files found"
            session.commit()
            return

        job.stage = "analysis"
        session.commit()

        all_graphs = []
        for file_path, code in file_map.items():
            ir_file = _parse_file(file_path, code)
            ir_dict = ir_file.to_dict()
            ir_key = f"{settings.s3_prefix}/project-{job.project_id}/ir/{job.id}/{file_path}.json"
            ir_uri = s3_put_json(settings.s3_bucket, ir_key, ir_dict)

            session.add(IrArtifact(artifact_id=artifact.id, s3_uri=ir_uri, language=ir_dict["language"]))
            session.commit()

            _persist_entities(session, job.project_id, ir_dict)

            call_graph = build_call_graph(ir_dict)
            cfg = build_cfg(ir_dict)
            dep_graph = build_dependency_graph(ir_dict)
            dfg = build_dfg(ir_dict)
            merged = merge_graphs([call_graph, cfg, dep_graph, dfg])
            all_graphs.append(merged)

            _persist_embeddings(session, job.project_id, artifact.id, file_path, code)

        if all_graphs:
            merged = merge_graphs(all_graphs)
            graph_snapshot = {"nodes": merged.nodes, "edges": merged.edges}
            graph_key = f"{settings.s3_prefix}/project-{job.project_id}/graphs/{job.id}.json"
            graph_uri = s3_put_json(settings.s3_bucket, graph_key, graph_snapshot)
            session.add(GraphVersion(project_id=job.project_id, s3_uri=graph_uri))
            session.commit()
            _persist_graph(session, job.project_id, graph_snapshot)

        job.status = "completed"
        job.stage = "done"
        session.commit()
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        session.commit()
        raise
