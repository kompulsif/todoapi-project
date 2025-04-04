from contextlib import contextmanager

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from collections.abc import Generator
from typing import Any
from config import (
    DB_CONNECTION_STRING,
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT,
)

Base = declarative_base()
engine = create_engine(
    url=DB_CONNECTION_STRING,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_recycle=DB_POOL_RECYCLE,
    pool_timeout=DB_POOL_TIMEOUT,
    echo=False,
)


@contextmanager
def db_session() -> Generator[Session, Any, None]:
    """
    Veritabaninda oturum olusturur
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        session.expire_on_commit = False
        yield session
        session.commit()

    except Exception as exc:
        session.expire_on_commit = True
        session.rollback()
        session.expire_all()
        raise exc

    finally:
        session.close()
