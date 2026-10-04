from datetime import datetime

from pydantic import BaseModel, ConfigDict

class IncidentCreate(BaseModel):
    title: str 
    description: str
    severity: str 
    service: str

class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str 
    severity: str
    status: str
    service: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    service: str | None = None