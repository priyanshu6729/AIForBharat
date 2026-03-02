from pydantic import BaseModel, Field


class ProgressUpdateRequest(BaseModel):
    lesson_id: int
    status: str = Field(..., min_length=1)


class ProgressItem(BaseModel):
    lesson_id: int
    status: str
    updated_at: str


class ProgressListResponse(BaseModel):
    progress: list[ProgressItem]


class ProgressUpdateResponse(BaseModel):
    lesson_id: int
    status: str
    updated_at: str
