from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.models import LearningPath, Lesson
from app.schemas.learn import LearningPathSummary, LearningPathDetail, LessonSummary
from app.services.seed import ensure_learning_paths

router = APIRouter()


@router.get("/api/learn/paths", response_model=list[LearningPathSummary])
def list_learning_paths(
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    ensure_learning_paths(session)
    paths = session.query(LearningPath).order_by(LearningPath.created_at.asc()).all()
    response: list[LearningPathSummary] = []
    for path in paths:
        lesson_count = (
            session.query(Lesson).filter(Lesson.path_id == path.id).count()
        )
        response.append(
            LearningPathSummary(
                id=path.id,
                title=path.title,
                description=path.description,
                difficulty=path.difficulty,
                lesson_count=lesson_count,
            )
        )
    return response


@router.get("/api/learn/paths/{path_id}", response_model=LearningPathDetail)
def get_learning_path(
    path_id: int,
    claims=Depends(get_current_user),
    session: Session = Depends(get_db),
):
    ensure_learning_paths(session)
    path = session.get(LearningPath, path_id)
    if path is None:
        raise HTTPException(status_code=404, detail="learning path not found")

    lessons = (
        session.query(Lesson)
        .filter(Lesson.path_id == path.id)
        .order_by(Lesson.order.asc())
        .all()
    )
    lesson_payload = [
        LessonSummary(
            id=lesson.id,
            title=lesson.title,
            content=lesson.content,
            order=lesson.order,
        )
        for lesson in lessons
    ]

    return LearningPathDetail(
        id=path.id,
        title=path.title,
        description=path.description,
        difficulty=path.difficulty,
        lessons=lesson_payload,
    )
