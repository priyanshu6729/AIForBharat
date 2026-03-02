from __future__ import annotations

import json
import logging
from typing import Any

import boto3

from libs.common.config import settings

logger = logging.getLogger(__name__)


def s3_client():
    return boto3.client("s3", region_name=settings.aws_region)


def sqs_client():
    return boto3.client("sqs", region_name=settings.aws_region)


def bedrock_client():
    return boto3.client("bedrock-runtime", region_name=settings.bedrock_region)


def s3_put_json(bucket: str, key: str, payload: dict[str, Any]) -> str:
    body = json.dumps(payload).encode("utf-8")
    s3 = s3_client()
    s3.put_object(Bucket=bucket, Key=key, Body=body)
    uri = f"s3://{bucket}/{key}"
    logger.info("Uploaded JSON to %s", uri)
    return uri


def s3_put_bytes(bucket: str, key: str, body: bytes) -> str:
    s3 = s3_client()
    s3.put_object(Bucket=bucket, Key=key, Body=body)
    uri = f"s3://{bucket}/{key}"
    logger.info("Uploaded bytes to %s", uri)
    return uri


def s3_get_bytes(bucket: str, key: str) -> bytes:
    s3 = s3_client()
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def sqs_send(queue_url: str, payload: dict[str, Any]) -> None:
    sqs = sqs_client()
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(payload))
