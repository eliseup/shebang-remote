from contextlib import asynccontextmanager

from fastapi import FastAPI

from sqlalchemy import select

from server.database import get_db_engine, DBSession
from server.models import BaseModel, CommandStatusReference
from server.views import router as server_views_router


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
