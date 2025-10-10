from datetime import datetime

from pydantic import BaseModel


class MachineSchema(BaseModel):
    external_id: str
    name: str
    last_seen: datetime

    class Config:
        from_attributes = True


class MachineResponse(MachineSchema):
    id: int
    created_at: datetime
    updated_at: datetime
