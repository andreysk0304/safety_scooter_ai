from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from src.database_models import Base


class Database:
    def __init__(self, database_url: str = None):
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )

        Base.metadata.create_all(self.engine)

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )


    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def get_raw_connection(self):
        return self.engine.raw_connection()