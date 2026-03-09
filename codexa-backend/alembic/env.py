from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.db import Base
from app.models import models  # noqa: F401

config = context.config

# Set the sqlalchemy.url from environment variable
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url():
    url = os.getenv("DATABASE_URL", "postgresql+psycopg2://codexa:codexa@localhost:5432/codexa")
    # Railway can provide postgres://; SQLAlchemy expects postgresql+psycopg2://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


# NOTE:
# Avoid config.set_main_option("sqlalchemy.url", ...) because ConfigParser
# interprets '%' characters in URL-encoded passwords (e.g. %40) as interpolation.
# We pass DATABASE_URL directly in run_migrations_offline/online below.


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(
        get_url(),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
