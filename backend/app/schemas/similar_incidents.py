from pydantic import BaseModel


class SimilarIncident(BaseModel):
    incident_id: int
    title: str
    service: str
    severity: str
    status: str
    similarity: str
    reason: str
    relevant_pattern: str


class SimilarIncidentsResponse(BaseModel):
    incidents: list[SimilarIncident]
