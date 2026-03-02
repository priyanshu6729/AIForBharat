from pydantic import BaseModel, Field


class ExecuteRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(..., pattern="^(python|javascript)$")


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    execution_time: float
    complexity_hint: str
