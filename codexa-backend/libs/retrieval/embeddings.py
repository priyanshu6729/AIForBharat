from __future__ import annotations

import hashlib
import json
import logging
import math
from typing import Iterable

from libs.common.aws import bedrock_client
from libs.common.config import settings

logger = logging.getLogger(__name__)


def _hash_to_vector(text: str, dim: int = 1536) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    ints = [int(digest[i : i + 4], 16) for i in range(0, len(digest), 4)]
    vec = [0.0] * dim
    for i, value in enumerate(ints):
        vec[i % dim] += value / 65535.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed_texts(texts: list[str]) -> list[list[float]]:
    try:
        client = bedrock_client()
        embeddings: list[list[float]] = []
        for text in texts:
            payload = {"inputText": text}
            response = client.invoke_model(
                modelId=settings.titan_embedding_model_id,
                body=json.dumps(payload),
                accept="application/json",
                contentType="application/json",
            )
            body = json.loads(response["body"].read())
            embeddings.append(body["embedding"])
        return embeddings
    except Exception as exc:
        logger.warning("Falling back to hash embeddings: %s", exc)
        return [_hash_to_vector(text) for text in texts]
