from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_engineer
from app.models.incident import Incident
from app.models.log import Log
from app.schemas.analysis import IncidentAnalysisResponse
from app.services.incident_analysis import (
    IncidentAnalysisConfigError,
    IncidentAnalysisError,
    analyze_incident,
)

router = APIRouter(prefix="/incidents", tags=["Analysis"])


@router.post(
    "/{incident_id}/analyze",
    response_model=IncidentAnalysisResponse,
    dependencies=[Depends(require_engineer)],
)
def analyze_incident_route(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    logs = (
        db.query(Log)
        .filter(Log.incident_id == incident_id)
        .order_by(Log.timestamp.asc())
        .all()
    )

    try:
        return analyze_incident(incident, logs)
    except IncidentAnalysisConfigError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ANTHROPIC_API_KEY is not configured",
        )
    except IncidentAnalysisError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Incident analysis service failed",
        )
