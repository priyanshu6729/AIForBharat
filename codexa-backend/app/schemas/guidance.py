from pydantic import BaseModel, Field, model_validator


class GuidanceRequest(BaseModel):
    user_question: str = Field(default="")
    code_context: str = Field(default="")
    ast_context: dict = Field(default_factory=dict)
    session_id: int | None = None
    goal: str | None = None
    guidance_level: int | None = Field(default=0, ge=0, le=5)
    # Chat-style alias — frontend stream.ts sends 'message'
    message: str | None = Field(default=None)

    @model_validator(mode="after")
    def coerce_message_to_question(self) -> "GuidanceRequest":
        if not self.user_question and self.message:
            self.user_question = self.message
        if not self.user_question:
            raise ValueError("user_question or message is required")
        return self


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
