import datetime

from dataclasses import dataclass

from sqlalchemy import func, MetaData, String, Text, TIMESTAMP, DATE, ForeignKey
from sqlalchemy.orm import (DeclarativeBase, declared_attr, Mapped,
                            scoped_session, mapped_column, relationship)


@dataclass
class BaseTypes:
    """Custom types that can be used in SQLAlchemy Mapper classes."""
    type str12 = str
    type str45 = str
    type str255 = str
    type text = str
    type timestamp = datetime.datetime
    type date = datetime.date


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
    }

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

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

    # Custom parameter to facilitate the use of the database session.
    session: scoped_session = None

    @declared_attr.directive
    def __tablename__(cls):
        table = ''.join(f"_{i}" if i.isupper() else i for i in cls.__name__)
        return table.lstrip('_').lower()


class Machine(BaseModel):
    """The machine model class."""
    external_id: Mapped[BaseTypes.str255] = mapped_column(unique=True, nullable=False)
    name: Mapped[BaseTypes.str45]
    last_seen: Mapped[BaseTypes.timestamp]

    commands: Mapped[list['Command']] = relationship(
        back_populates='machine',
    )


class Script(BaseModel):
    """The script model class."""
    name: Mapped[BaseTypes.str45] = mapped_column(unique=True, nullable=False)
    content: Mapped[BaseTypes.text]


class CommandStatusReference(BaseModel):
    """
    The command status reference model class.
    """
    title: Mapped[BaseTypes.str45] = mapped_column(nullable=False, unique=True)
    title_internal: Mapped[BaseTypes.str45] = mapped_column(nullable=False, unique=True)


class Command(BaseModel):
    """The command model class."""
    machine_id: Mapped[int] = mapped_column(
        ForeignKey('machine.id', ondelete='CASCADE',)
    )

    status_id: Mapped[int] = mapped_column(
        ForeignKey('command_status_reference.id', ondelete='SET NULL',)
    )

    machine: Mapped[Machine] = relationship(back_populates='commands')
    status: Mapped[CommandStatusReference] = relationship()

    script_name: Mapped[BaseTypes.text]
    output: Mapped[BaseTypes.text | None]
