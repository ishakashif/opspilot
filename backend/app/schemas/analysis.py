from pydantic import BaseModel


class IncidentAnalysisResponse(BaseModel):
    root_cause: str
    evidence: list[str]
    recommended_actions: list[str]
    confidence: str
