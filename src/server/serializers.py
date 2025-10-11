import json
from datetime import datetime

from pydantic import BaseModel, field_validator


class DefaultResponseSchemaMixin:
    created_at: datetime
    updated_at: datetime


class MachineSchema(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class MachineResponseSchema(DefaultResponseSchemaMixin, MachineSchema):
    last_seen: datetime


class ScriptSchema(BaseModel):
    name: str
    content: str

    @field_validator('name', mode='before')
    def normalize_name(cls, value):
        return value.replace(' ', '').lower().strip()

    class Config:
        from_attributes = True


class ScriptResponseSchema(DefaultResponseSchemaMixin, ScriptSchema):
    pass


class CommandStatusReferenceResponseSchema(DefaultResponseSchemaMixin, BaseModel):
    title: str
    title_internal: str


class CommandSchema(BaseModel):
    machine_id: str
    script_name: str

    class Config:
        from_attributes = True


class CommandResponseSchema(DefaultResponseSchemaMixin, CommandSchema):
    id: int
    status: CommandStatusReferenceResponseSchema
    script: ScriptSchema
    output: str | None


class CommandResultSchema(BaseModel):
    output: str | None

    @field_validator('output', mode='before')
    def normalize_output(cls, value):
        try:
            return json.dumps(value)
        except TypeError:
            return value
