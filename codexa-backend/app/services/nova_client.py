from __future__ import annotations
import json
import logging
from typing import Any
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)

def _bedrock_client():
    return boto3.client("bedrock-runtime", region_name=settings.bedrock_region)

def _invoke_nova(prompt: str, max_tokens: int = 500) -> str:
    """Invoke AWS Bedrock Nova model with proper error handling"""
    if not settings.nova_model_id:
        raise RuntimeError("NOVA_MODEL_ID not configured")
    
    try:
        client = _bedrock_client()
        
        # Format for Nova models
        payload = {
            "schemaVersion": "messages-v1",
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        response = client.invoke_model(
            modelId=settings.nova_model_id,
            body=json.dumps(payload),
            accept="application/json",
            contentType="application/json",
        )
        
        body = json.loads(response["body"].read())
        
        # Parse Nova response format
        if isinstance(body, dict) and "output" in body:
            if isinstance(body["output"], dict) and "message" in body["output"]:
                content = body["output"]["message"].get("content", [])
                if content and isinstance(content, list) and len(content) > 0:
                    return content[0].get("text", "")
        
        logger.warning(f"Unexpected Nova response format: {body}")
        return ""
        
    except ClientError as e:
        logger.error(f"Bedrock API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Nova invocation error: {e}")
        raise

def analyze_with_nova(code: str, language: str, ast: dict) -> dict | None:
    """
    Analyze code with AWS Nova - provides insights without giving solutions
    """
    try:
        prompt = (
            "You are Codexa, a Socratic programming tutor. Analyze this code and provide:\n"
            "1. A brief summary of what the code does (2-3 sentences)\n"
            "2. 3-4 guiding questions or hints to help understand it better\n"
            "3. Any potential issues or edge cases to consider\n"
            "DO NOT provide solutions, refactored code, or complete implementations.\n"
            "DO NOT write code snippets longer than 5 lines.\n\n"
            f"Language: {language}\n"
            f"Code:\n{code}\n\n"
            f"AST Structure: {json.dumps(ast, indent=2)}\n\n"
            "Respond in JSON format:\n"
            '{"summary": "...", "hints": ["...", "..."], "issues": ["...", "..."]}'
        )
        
        response_text = _invoke_nova(prompt, max_tokens=600)
        
        # Try to parse as JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If not valid JSON, structure it manually
            return {
                "summary": response_text[:200] if response_text else "Analysis complete.",
                "hints": ["Review the code structure and flow"],
                "issues": []
            }
            
    except Exception as e:
        logger.warning(f"Nova analysis failed: {e}")
        return None

def guidance_with_nova(
    question: str,
    code: str,
    ast: dict,
    goal: str | None = None,
    guidance_level: int = 0,
    explicit_full: bool = False,
) -> str | None:
    """
    Provide Socratic guidance - NEVER gives full solutions
    """
    # Override: Never allow level 5 full solutions
    if guidance_level >= 5:
        guidance_level = 4
        logger.info("Guidance level capped at 4 to prevent full solutions")
    
    goal_line = f"Learning goal: {goal}\n" if goal else ""
    
    level_instructions = {
        0: "Ask 1-2 clarifying questions about inputs, outputs, or constraints. Do not suggest solutions.",
        1: "Provide a high-level conceptual hint (one sentence). No code, no algorithms.",
        2: "Give a 3-4 step outline of the approach. No code, no implementation details.",
        3: "Provide structured pseudocode steps (5-7 lines). Use generic terms, not actual syntax.",
        4: "Give a minimal code hint (maximum 8 lines) showing ONE specific technique. Do not solve the whole problem.",
    }
    
    instruction = level_instructions.get(guidance_level, level_instructions[1])
    
    prompt = (
        "You are Codexa, a Socratic programming tutor that helps students learn by guiding, not solving.\n"
        "STRICT RULES:\n"
        "- NEVER provide a complete solution\n"
        "- NEVER write full function implementations\n"
        "- NEVER solve the entire problem\n"
        "- Maximum code shown: 8 lines for level 4, 0 lines for levels 0-3\n"
        "- Focus on teaching through questions and hints\n\n"
        f"Current guidance level: {guidance_level}\n"
        f"Your task: {instruction}\n\n"
        f"{goal_line}"
        f"Student question: {question}\n\n"
        f"Code context:\n{code}\n\n"
        f"AST info: {json.dumps(ast)}\n\n"
        "Provide your response following the guidance level rules strictly."
    )
    
    try:
        response = _invoke_nova(prompt, max_tokens=400)
        
        # Safety check: if response is too long or looks like full solution, truncate
        if len(response) > 800 or response.count('\n') > 15:
            logger.warning("Response too long, truncating to prevent full solution")
            lines = response.split('\n')[:10]
            response = '\n'.join(lines) + "\n\n💡 Try implementing this yourself and ask for clarification if needed!"
        
        return response.strip()
        
    except Exception as exc:
        logger.warning("Nova guidance failed: %s", exc)
        return None
