import datetime

from dataclasses import dataclass

from sqlalchemy import func, MetaData, String, Text, TIMESTAMP, DATE, ForeignKey, BigInteger
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column, relationship


@dataclass
class BaseTypes:
    """Custom types that can be used in SQLAlchemy Mapper classes."""
    type str12 = str
    type str45 = str
    type str255 = str
    type text = str
    type timestamp = datetime.datetime
    type date = datetime.date
    type bigint = int


NAMING_CONVENTION = {
    "ix": "ix__%(column_0_label)s",
    "uq": "uq__%(table_name)s__%(column_0_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
    "pk": "pk__%(table_name)s"
}

def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class BaseModel(DeclarativeBase):
    """Base model class that offers common functionality."""
    __abstract__ = True

    metadata: MetaData = MetaData(naming_convention=NAMING_CONVENTION)

    type_annotation_map = {
        BaseTypes.str12: String(12),
        BaseTypes.str45: String(45),
        BaseTypes.str255: String(255),
        BaseTypes.text: Text(),
        BaseTypes.timestamp: TIMESTAMP(timezone=True),
        BaseTypes.date: DATE,
        BaseTypes.bigint: BigInteger,
    }

    created_at: Mapped[BaseTypes.timestamp] = mapped_column(
        default=utc_now,
        server_default=func.now(),
    )

    # We are not using server_onupdate here because PostgreSQL doesn't have native
    # ON UPDATE fields like MySQL's ON UPDATE CURRENT_TIMESTAMP
    updated_at: Mapped[BaseTypes.timestamp] = mapped_column(
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
    )

    @declared_attr.directive
    def __tablename__(cls):
        table = ''.join(f"_{i}" if i.isupper() else i for i in cls.__name__)
        return table.lstrip('_').lower()


class Machine(BaseModel):
    """
    The machine model class.

    Represents a machine (agent).

    Attributes:
        - external_id: Unique identifier for the machine (e.g., UUID or external system ID)
        - name: Human-readable name for the machine
        - last_seen: Timestamp of the last time the machine checked in
        - commands: List of commands assigned to this machine
    """
    id: Mapped[BaseTypes.str255] = mapped_column(primary_key=True)
    name: Mapped[BaseTypes.str45]
    last_seen: Mapped[BaseTypes.timestamp]

    commands: Mapped[list['Command']] = relationship(
        back_populates='machine',
    )


class Script(BaseModel):
    """
    The script model class.

    Represents a script that can be executed on a machine.

    Attributes:
        - name: Unique name for the script
        - content: The actual script content (e.g., any Linux command.)

    Usage:
        Scripts are assigned to commands for execution on machines.
    """
    name: Mapped[BaseTypes.str45] = mapped_column(primary_key=True)
    content: Mapped[BaseTypes.text]


class CommandStatusReference(BaseModel):
    """
    The command status reference model class.

    Represents a reference table for command statuses.

    Attributes:
        - title: Human-readable status (e.g., 'Pending', 'Completed')
        - title_internal: Internal system status identifier (must be unique)

    Usage:
        Used to track and categorize the status of commands.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[BaseTypes.str45] = mapped_column(nullable=False, unique=True)
    title_internal: Mapped[BaseTypes.str45] = mapped_column(nullable=False, unique=True)


class Command(BaseModel):
    """
    The command model class.

    Represents a command to be executed on a specific machine.

    Each Command is associated with a Machine and a Script,
    and tracks its execution status via CommandStatusReference.

    Relationships:
        - machine: The Machine this command is assigned to.
        - script: The Script to be executed on the machine.
        - status: Current execution status of the command.

    Usage:
        This model is used by the API endpoint `GET /commands/{machine_id}`
        to retrieve pending commands for a specific agent/machine.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    machine_id: Mapped[BaseTypes.str255] = mapped_column(
        ForeignKey('machine.id', ondelete='CASCADE',)
    )

    script_name: Mapped[BaseTypes.str45] = mapped_column(
        ForeignKey('script.name', ondelete='CASCADE',)
    )

    status_id: Mapped[int] = mapped_column(
        ForeignKey('command_status_reference.id', ondelete='SET NULL',)
    )

    machine: Mapped[Machine] = relationship(back_populates='commands')
    script: Mapped[Script] = relationship()
    status: Mapped[CommandStatusReference] = relationship()

    output: Mapped[BaseTypes.text | None]


class DiscordAuthorizedUser(BaseModel):
    """
    The Discord Authorized Users model class used by Discord bot to store authorized users IDs.
    """
    author_id: Mapped[BaseTypes.bigint] = mapped_column(primary_key=True)
