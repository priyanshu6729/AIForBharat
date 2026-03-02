"""learning paths and progress

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-28 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "learning_paths",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("path_id", sa.Integer(), sa.ForeignKey("learning_paths.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_lessons_path_id", "lessons", ["path_id"], unique=False)

    op.create_table(
        "progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_progress_user_id", "progress", ["user_id"], unique=False)
    op.create_index("ix_progress_lesson_id", "progress", ["lesson_id"], unique=False)

    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_achievements_user_id", "achievements", ["user_id"], unique=False)


def downgrade():
    op.drop_index("ix_achievements_user_id", table_name="achievements")
    op.drop_table("achievements")
    op.drop_index("ix_progress_lesson_id", table_name="progress")
    op.drop_index("ix_progress_user_id", table_name="progress")
    op.drop_table("progress")
    op.drop_index("ix_lessons_path_id", table_name="lessons")
    op.drop_table("lessons")
    op.drop_table("learning_paths")
