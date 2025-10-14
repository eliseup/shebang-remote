import logging

from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import select

from server.database import get_db_engine, DBSession
from server.models import BaseModel, CommandStatusReference
from server.views import router as server_views_router


# Logging setup
logging_file = Path('../logs/app.log')

if not logging_file.parent.exists():
    logging_file.parent.mkdir()

logger = logging.getLogger('server')

logging_handler = RotatingFileHandler(
    filename=logging_file,
    maxBytes=5000000,
    backupCount=3,
)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logging_handler.setLevel(logging.INFO)
logging_handler.setFormatter(formatter)
logger.addHandler(logging_handler)

def post_init_database() -> None:
    """Perform post-initialization tasks for the database."""

    # Populates CommandStatusReference table.
    command_status = [
        ('Pending', 'pending'),
        ('Completed', 'completed'),
    ]

    with DBSession() as session:
        for status in command_status:
            if not session.scalar(
                    select(CommandStatusReference).filter_by(title_internal=status[1])):
                session.add(
                    CommandStatusReference(
                        title=status[0],
                        title_internal=status[1],
                    )
                )

        session.commit()

def init_database() -> None:
    """Initialize the database creating tables if they do not exist."""
    BaseModel.metadata.create_all(bind=get_db_engine())

    # Run post-initialization tasks.
    post_init_database()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()

    yield

app = FastAPI(lifespan=lifespan)

# Register routes
app.include_router(server_views_router)
