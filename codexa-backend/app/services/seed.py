from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.models import LearningPath, Lesson


SEED_PATHS = [
    {
        "title": "Python Foundations",
        "description": "Master variables, control flow, and functions through guided practice.",
        "difficulty": "Beginner",
        "lessons": [
            {
                "title": "Variables & Data Types",
                "content": "Practice storing values and predicting output from type changes.",
                "order": 1,
            },
            {
                "title": "Control Flow",
                "content": "Trace if/else logic and predict which branch executes.",
                "order": 2,
            },
            {
                "title": "Functions & Scope",
                "content": "Identify inputs, outputs, and how scope changes variable behavior.",
                "order": 3,
            },
        ],
    },
    {
        "title": "JavaScript Essentials",
        "description": "Understand core syntax, loops, and working with arrays.",
        "difficulty": "Beginner",
        "lessons": [
            {
                "title": "JavaScript Syntax",
                "content": "Spot missing semicolons and learn how JS evaluates expressions.",
                "order": 1,
            },
            {
                "title": "Loops in JS",
                "content": "Explain how for/while loops progress through arrays.",
                "order": 2,
            },
            {
                "title": "Working with Arrays",
                "content": "Use map/filter to transform data and explain outputs.",
                "order": 3,
            },
        ],
    },
]


def ensure_learning_paths(session: Session) -> None:
    existing = session.query(LearningPath).count()
    if existing > 0:
        return

    for path in SEED_PATHS:
        learning_path = LearningPath(
            title=path["title"],
            description=path["description"],
            difficulty=path["difficulty"],
        )
        session.add(learning_path)
        session.flush()
        for lesson in path["lessons"]:
            session.add(
                Lesson(
                    path_id=learning_path.id,
                    title=lesson["title"],
                    content=lesson["content"],
                    order=lesson["order"],
                )
            )
    session.commit()
