"""Database connection and session lifecycle management."""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import AppConfig


def _enable_sqlite_pragmas(dbapi_con, con_record):
    """Enforce foreign key constraints and configure WAL mode for SQLite."""
    cursor = dbapi_con.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.close()


class DatabaseManager:
    """Manages SQLAlchemy 2.0 Engine and Session lifecycle."""

    def __init__(self, db_url: str, echo: bool = False) -> None:
        self.db_url = db_url
        self.engine: Engine = create_engine(
            self.db_url,
            echo=echo,
            future=True,
            connect_args={"check_same_thread": False} if "sqlite" in self.db_url else {},
        )

        if "sqlite" in self.db_url and ":memory:" not in self.db_url:
            event.listen(self.engine, "connect", _enable_sqlite_pragmas)
        elif "sqlite" in self.db_url and ":memory:" in self.db_url:
            # Memory DB also needs foreign keys enabled
            event.listen(self.engine, "connect", lambda con, _: con.cursor().execute("PRAGMA foreign_keys = ON;"))

        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    @classmethod
    def from_config(cls, config: AppConfig, echo: bool = False) -> "DatabaseManager":
        """Instantiate DatabaseManager using AppConfig."""
        config.database_dir.mkdir(parents=True, exist_ok=True)
        return cls(config.sqlite_url, echo=echo)

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self) -> None:
        """Create all tables defined in models (useful for testing and initial bootstrap)."""
        from app.infrastructure.database.models.base import Base
        Base.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        """Drop all tables."""
        from app.infrastructure.database.models.base import Base
        Base.metadata.drop_all(self.engine)
