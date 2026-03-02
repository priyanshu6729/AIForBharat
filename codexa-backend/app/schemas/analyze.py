from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(..., pattern="^(python|javascript)$")


class AnalyzeResponse(BaseModel):
    ast: dict
    ai_analysis: dict | None = None
