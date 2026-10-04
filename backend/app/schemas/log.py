from datetime import datetime

from pydantic import BaseModel, ConfigDict

class LogCreate(BaseModel):
    level: str
    message: str
    source: str

class LogResponse(BaseModel):
    id: int
    incident_id: int
    level: str
    message: str
    source: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
