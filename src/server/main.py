from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sqlalchemy import create_engine, Engine, NullPool
from sqlalchemy.orm import scoped_session, sessionmaker, Session

from server.models import BaseModel
from server.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Starting server...')
    conn = settings.SQLALCHEMY_DATABASE_URI
    engine = create_engine(
        conn, echo=False, echo_pool=False, pool_recycle=50, pool_size=7, max_overflow=10
    )

    BaseModel.session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    #with engine.begin() as conn:
    #    await conn.execute(BaseModel.metadata.create_all)

    BaseModel.metadata.create_all(bind=engine)

    yield
    print('Stopping server...')
    BaseModel.session.remove()


app = FastAPI(lifespan=lifespan)

@app.get('/machines')
async def get_machines():
    """
    Return active machines.
    Active machines are those that sent a 'ping' in the last 5 minutes.
    """
    return {'message': 'machines active'}


@app.post('/register_machine')
async def create_update_machines(payload: dict[str, Any]):
    """
    Create or update machines.
    """


@app.post('/scripts')
async def create_scripts(payload: dict[str, Any]):
    """
    Create a script.
    """


@app.post('/execute')
async def execute(payload: dict[str, Any]):
    """
    Schedule a command for a machine.
    """


@app.get('/commands/{machine_id}')
async def get_commands(machine_id: int):
    """
    Get pending commands for an agent.
    """


@app.post('/commands/{command_id}/result')
async def post_command(command_id: int):
    """
    Receives a result of an executed command.
    """
