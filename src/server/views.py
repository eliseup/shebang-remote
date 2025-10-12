import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, InstrumentedAttribute
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from server.database import get_db_session
from server.models import Machine, CommandStatusReference, Command, Script, BaseModel
from server.serializers import (MachineSchema, MachineResponseSchema, CommandSchema,
                                CommandResponseSchema, ScriptResponseSchema, ScriptSchema,
                                CommandResultSchema)


def get_object_or_404(
        session: Session,
        model: BaseModel,
        column: InstrumentedAttribute,
        id_: str | int
):
    obj = session.scalar(select(model).filter(column == id_))

    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} with id {id_} was not found"
        )

    return obj

router = APIRouter()

@router.get('/machines', response_model=list[MachineResponseSchema])
async def list_machines(session: Session = Depends(get_db_session)):
    """
    Return active machines.
    Active machines are those that sent a 'ping' in the last 5 minutes.
    """
    deadline = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)

    machines = session.scalars(select(Machine).filter(
        Machine.last_seen >= deadline,
    )).all()

    return machines

@router.post('/register_machine', response_model=MachineResponseSchema)
async def create_update_machine(
        model: MachineSchema,
        session: Session = Depends(get_db_session)
):
    """
    Create or update machines.
    """
    existing_machine = session.scalar(
        select(Machine).filter(Machine.id == model.id)
    )

    now = datetime.datetime.now(datetime.timezone.utc)

    if not existing_machine:
        # Create new machine.
        new_machine = Machine(**model.model_dump())
        new_machine.last_seen = now

        session.add(new_machine)
        session.commit()
        session.refresh(new_machine)

        return new_machine

    # Update existing machine.
    for key, value in model.model_dump().items():
        setattr(existing_machine, key, value)

    existing_machine.last_seen = now

    session.commit()
    session.refresh(existing_machine)
    return existing_machine

@router.post('/scripts', response_model=ScriptResponseSchema)
async def create_script(
        model: ScriptSchema,
        session: Session = Depends(get_db_session)
):
    """
    Create a script with an uniq name and its content.
    """
    new_script = Script(**model.model_dump())
    session.add(new_script)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Script with name {model.name} already exists.'
        )

    session.refresh(new_script)

    return new_script

@router.post('/execute', response_model=CommandResponseSchema)
async def schedule_machine_command(
        model: CommandSchema,
        session: Session = Depends(get_db_session)
):
    """
    Schedule a command for a machine.
    """
    pending_status = session.scalar(select(CommandStatusReference).filter(
        CommandStatusReference.title_internal == 'pending'
    ))

    # Check if script and machine exist.
    get_object_or_404(
        session=session, model=Machine, column=Machine.id, id_=model.machine_id
    )

    get_object_or_404(
        session=session, model=Script, column=Script.name, id_=model.script_name
    )

    # Create and persist command.
    new_command = Command(**model.model_dump())
    new_command.status = pending_status

    session.add(new_command)
    session.commit()
    session.refresh(new_command)

    return new_command

@router.get('/commands/{machine_id}', response_model=list[CommandResponseSchema])
async def list_pending_commands(
        machine_id: str,
        session: Session = Depends(get_db_session)
):
    """
    Get pending commands for an agent.
    """
    now = datetime.datetime.now(datetime.timezone.utc)


    machine = get_object_or_404(
        session=session, model=Machine, column=Machine.id, id_=machine_id
    )

    machine.last_seen = now
    session.commit()
    session.refresh(machine)

    pending_commands = session.scalars(
        select(Command).join(CommandStatusReference).filter(
            Command.machine_id == machine_id,
            CommandStatusReference.title_internal == 'pending'
        )
    ).all()

    return pending_commands

@router.post('/commands/{command_id}/result')
async def store_command_result(
        command_id: int,
        result: CommandResultSchema,
        session: Session = Depends(get_db_session)
):
    """
    Stores a result of an executed command.
    """
    completed_status = session.scalar(select(CommandStatusReference).filter(
        CommandStatusReference.title_internal == 'completed'
    ))

    existing_command = get_object_or_404(
        session=session, model=Command, column=Command.id, id_=command_id
    )

    # Updates the existing_command with the given result data.
    existing_command.output = result.output
    existing_command.status = completed_status

    session.add(existing_command)
    session.commit()
    session.refresh(existing_command)
