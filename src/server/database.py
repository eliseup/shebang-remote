from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from server.config import settings


def get_db_engine() -> Engine:
    conn = settings.SQLALCHEMY_DATABASE_URI

    engine = create_engine(
        conn, echo=False, echo_pool=False, pool_recycle=60, pool_size=7, max_overflow=10
    )

    return engine

DBSession = sessionmaker(autocommit=False, autoflush=False, bind=get_db_engine())

def get_db_session() -> Session:
    session = DBSession()
    try:
        yield session
    finally:
        session.close()
