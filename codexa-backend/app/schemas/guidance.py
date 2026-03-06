from pydantic import BaseModel, Field


class GuidanceRequest(BaseModel):
    user_question: str = Field(..., min_length=1)
    code_context: str = Field(default="")
    ast_context: dict = Field(default_factory=dict)
    session_id: int | None = None
    goal: str | None = None
    guidance_level: int | None = Field(default=0, ge=0, le=5)


class GuidanceResponse(BaseModel):
    response: str
    session_id: int | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    code_context: str | None = None
    session_id: int | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: int
