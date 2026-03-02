from sqlalchemy import text

from libs.common.db import Base, engine


def main():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(conn)
    print("Database initialized")


if __name__ == "__main__":
    main()
