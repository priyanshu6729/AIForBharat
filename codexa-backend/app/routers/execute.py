from fastapi import APIRouter, HTTPException
from app.schemas.execute import ExecuteRequest, ExecuteResponse
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/execute", response_model=ExecuteResponse)
def execute(payload: ExecuteRequest):
    """Execute code safely (Python only for now)"""
    try:
        logger.info(f"Executing {payload.language} code")
        
        if payload.language != "python":
            raise HTTPException(status_code=400, detail="Only Python execution is supported")
        
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        start_time = time.time()
        
        try:
            # WARNING: This is unsafe for production - use Docker/sandbox
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # Restricted builtins for safety
                safe_builtins = {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'sum': sum,
                    'max': max,
                    'min': min,
                    'abs': abs,
                    'pow': pow,
                    'round': round,
                    'enumerate': enumerate,
                    'zip': zip,
                }
                exec(payload.code, {"__builtins__": safe_builtins})
            
            execution_time = time.time() - start_time
            
            return ExecuteResponse(
                stdout=stdout_buffer.getvalue(),
                stderr=stderr_buffer.getvalue(),
                execution_time=execution_time,
                complexity_hint="Execution completed successfully"
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecuteResponse(
                stdout=stdout_buffer.getvalue(),
                stderr=f"Runtime error: {str(e)}",
                execution_time=execution_time,
                complexity_hint="Check your code for errors"
            )
            
    except Exception as e:
        logger.error(f"Execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
