from pydantic import BaseModel, Field


class SessionSaveRequest(BaseModel):
    session_id: int | None = None
    title: str
    language: str
    code: str
    visualization: dict = Field(default_factory=dict)
    chat_log: list[dict] = Field(default_factory=list)


class SessionSaveResponse(BaseModel):
    session_id: int


class SessionListItem(BaseModel):
    session_id: int
    title: str
    created_at: str


class SessionListResponse(BaseModel):
    sessions: list[SessionListItem]


class SessionResponse(BaseModel):
    session_id: int
    title: str
    language: str
    code: str
    visualization: dict
    chat_log: list[dict]
