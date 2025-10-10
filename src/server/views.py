from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.database import get_db_session
from server.models import Machine
from server.serializers import MachineSchema, MachineResponse

router = APIRouter()


@router.get('/machines')
async def get_machines():
    """
    Return active machines.
    Active machines are those that sent a 'ping' in the last 5 minutes.
    """
    return {'message': 'machines active'}


@router.post('/register_machine', response_model=MachineResponse)
async def create_update_machine(
        machine: MachineSchema,
        session: Session = Depends(get_db_session)
):
    """
    Create or update machines.
    """
    new_machine = Machine(**machine.model_dump())
    session.add(new_machine)
    session.commit()
    session.refresh(new_machine)

    return new_machine


@router.post('/scripts')
async def create_scripts(payload: dict[str, Any]):
    """
    Create a script.
    """


@router.post('/execute')
async def execute(payload: dict[str, Any]):
    """
    Schedule a command for a machine.
    """


@router.get('/commands/{machine_id}')
async def get_commands(machine_id: int):
    """
    Get pending commands for an agent.
    """


@router.post('/commands/{command_id}/result')
async def post_command(command_id: int):
    """
    Receives a result of an executed command.
    """
