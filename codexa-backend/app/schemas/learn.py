from pydantic import BaseModel


class LessonSummary(BaseModel):
    id: int
    title: str
    content: str
    order: int


class LearningPathSummary(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    lesson_count: int


class LearningPathDetail(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    lessons: list[LessonSummary]
