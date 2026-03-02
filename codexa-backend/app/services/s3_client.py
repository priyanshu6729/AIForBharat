import json
import os
import boto3

from app.core.config import settings


def s3_client():
    return boto3.client("s3", region_name=settings.aws_region)


def put_json(key: str, payload: dict) -> str:
    body = json.dumps(payload).encode("utf-8")
    try:
        client = s3_client()
        client.put_object(Bucket=settings.s3_bucket, Key=key, Body=body)
        return f"s3://{settings.s3_bucket}/{key}"
    except Exception:
        local_root = os.path.join(os.getcwd(), "local_storage")
        os.makedirs(local_root, exist_ok=True)
        local_path = os.path.join(local_root, key.replace("/", "_"))
        with open(local_path, "wb") as handle:
            handle.write(body)
        return f"local://{local_path}"


def get_json(s3_url: str) -> dict:
    if s3_url.startswith("local://"):
        path = s3_url.split("local://", 1)[1]
        if not os.path.exists(path):
            return {}
        with open(path, "rb") as handle:
            return json.loads(handle.read().decode("utf-8"))
    if s3_url.startswith("s3://"):
        _, rest = s3_url.split("s3://", 1)
        bucket, key = rest.split("/", 1)
        client = s3_client()
        obj = client.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read().decode("utf-8")
        return json.loads(body)
    return {}
