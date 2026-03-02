import json
import boto3

from app.core.config import settings
from app.services.ast_parser import parse_code


def invoke_analysis(code: str, language: str) -> dict:
    if settings.lambda_mode == "local":
        return parse_code(code, language)

    try:
        client = boto3.client("lambda", region_name=settings.aws_region)
        payload = json.dumps({"code": code, "language": language})
        response = client.invoke(
            FunctionName=settings.lambda_function_name,
            InvocationType="RequestResponse",
            Payload=payload,
        )
        body = response["Payload"].read().decode("utf-8")
        parsed = json.loads(body)
        if isinstance(parsed, dict) and "body" in parsed:
            return json.loads(parsed["body"])
        return parsed
    except Exception:
        return parse_code(code, language)
