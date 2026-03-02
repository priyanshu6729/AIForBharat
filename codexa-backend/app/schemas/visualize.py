from pydantic import BaseModel


class VisualizeRequest(BaseModel):
    ast: dict
    session_id: int | None = None


class VisualizeResponse(BaseModel):
    s3_url: str
    graph: dict
