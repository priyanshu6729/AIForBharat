from fastapi import APIRouter, HTTPException
from app.core.cache import LRUCache
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.ast_parser import parse_code_details
from app.services.ast_parser_fallback import parse_python_details
from app.services.nova_client import analyze_with_nova
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
_cache = LRUCache(max_size=128)


@router.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest):
    """Analyze code and return AST with AI insights"""
    try:
        cache_key = f"{payload.language}:{hash(payload.code)}"
        cached = _cache.get(cache_key)
        
        if cached:
            ast_result = cached
            logger.info("Using cached AST for %s", payload.language)
        else:
            logger.info("Parsing %s code", payload.language)
            try:
                ast_result = parse_code_details(payload.code, payload.language)
            except Exception as exc:
                logger.warning("Tree-sitter parse failed, falling back: %s", exc)
                if payload.language == "python":
                    ast_result = parse_python_details(payload.code)
                else:
                    ast_result = {"functions": [], "loops": [], "conditions": [], "dependencies": [], "calls": []}
            _cache.set(cache_key, ast_result)
        
        # Generate basic analysis
        ai_analysis = None
        try:
            ai_analysis = analyze_with_nova(payload.code, payload.language, ast_result)
        except Exception as exc:
            logger.warning("Nova analysis failed: %s", exc)

        if not ai_analysis:
            funcs = ast_result.get("functions", [])
            loops = ast_result.get("loops", [])
            conditions = ast_result.get("conditions", [])
            deps = ast_result.get("dependencies", [])
            calls = ast_result.get("calls", [])

            hints = [
                "Start by identifying the main input and output of the code.",
                "Trace the control flow in order and note where it branches.",
                "Check loop bounds and termination conditions carefully.",
            ]
            if funcs:
                hints.insert(0, f"Focus on `{funcs[0].get('name', 'the main function')}` first.")
            if deps:
                hints.append("Scan imports/dependencies for helpers you can reuse.")

            issues = []
            if not funcs and not loops and not conditions:
                issues.append("No major structural blocks detected. Is the code empty or incomplete?")

            ai_analysis = {
                "summary": f"Found {len(funcs)} functions, {len(loops)} loops, "
                           f"{len(conditions)} conditions, {len(deps)} dependencies, {len(calls)} calls.",
                "hints": hints,
                "issues": issues,
            }
        else:
            ai_analysis.setdefault("summary", "Analysis complete.")
            ai_analysis.setdefault("hints", [])
            ai_analysis.setdefault("issues", [])

        return AnalyzeResponse(ast=ast_result, ai_analysis=ai_analysis)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
