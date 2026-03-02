from __future__ import annotations

import json
import logging

from libs.common.aws import bedrock_client
from libs.common.config import settings

logger = logging.getLogger(__name__)


def generate_response(prompt: str) -> str:
    try:
        client = bedrock_client()
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }
        response = client.invoke_model(
            modelId=settings.bedrock_model_id,
            body=json.dumps(payload),
            accept="application/json",
            contentType="application/json",
        )
        body = json.loads(response["body"].read())
        return body["content"][0]["text"]
    except Exception as exc:
        logger.warning("Falling back to stub LLM response: %s", exc)
        return "[Stubbed response] Unable to reach Bedrock. Provide AWS credentials to enable LLM reasoning."
