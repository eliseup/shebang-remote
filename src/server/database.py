from contextlib import contextmanager

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
    """
    FastAPI dependency generator that provides a database session.

    Yields:
        Session: SQLAlchemy Session object.

    Usage in FastAPI endpoints:
        @app.get("/users")
        def read_users(db: Session = Depends(get_db_session)):
            return db.query(User).all()

    Notes:
        - The session is automatically closed by FastAPI after the request finishes.
        - Do not call this function directly outside FastAPI dependency injection
          (it returns a generator, not a Session object).
    """
    from server.main import logger

    session = DBSession()
    try:
        yield session
    except Exception as e:
        logger.exception('Failed to create session', exc_info=True)
        raise e
    finally:
        session.close()

@contextmanager
def get_db_session_ctx() -> Session:
    """
    Context manager for creating a database session usable outside FastAPI.

    Yields:
        Session: SQLAlchemy Session object.

    Usage:
        from database import get_db_session_ctx

        with get_db_session_ctx() as db:
            users = db.query(User).all()

    Notes:
        - Must be used with a `with` statement to ensure proper session cleanup.
        - Can be used in scripts, background tasks, or modules outside FastAPI.
    """
    from server.main import logger

    session = DBSession()
    try:
        yield session
    except Exception as e:
        logger.exception('Failed to create session', exc_info=True)
        raise e
    finally:
        session.close()
