from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import require_engineer
from app.models.incident import Incident
from app.models.log import Log
from app.schemas.similar_incidents import SimilarIncidentsResponse
from app.services.similar_incidents import (
    SimilarIncidentsConfigError,
    SimilarIncidentsError,
    find_similar_incidents,
)

router = APIRouter(prefix="/incidents", tags=["Similar Incidents"])

MAX_CANDIDATE_INCIDENTS = 20


@router.get(
    "/{incident_id}/similar",
    response_model=SimilarIncidentsResponse,
    dependencies=[Depends(require_engineer)],
)
def get_similar_incidents(
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
    candidates = _load_candidates(db, incident_id)
    if not candidates:
        return SimilarIncidentsResponse(incidents=[])

    try:
        return find_similar_incidents(incident, logs, candidates)
    except SimilarIncidentsConfigError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ANTHROPIC_API_KEY is Not Configured",
        )
    except SimilarIncidentsError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Similar Incidents Service Failed",
        )


def _load_candidates(
    db: Session,
    incident_id: int,
) -> list[tuple[Incident, list[Log]]]:
    incidents = (
        db.query(Incident)
        .filter(Incident.id != incident_id)
        .order_by(Incident.created_at.desc(), Incident.id.desc())
        .limit(MAX_CANDIDATE_INCIDENTS)
        .all()
    )
    if not incidents:
        return []

    candidate_ids = [candidate.id for candidate in incidents]
    logs = (
        db.query(Log)
        .filter(Log.incident_id.in_(candidate_ids))
        .order_by(Log.timestamp.asc(), Log.id.asc())
        .all()
    )
    logs_by_incident: dict[int, list[Log]] = {
        candidate.id: [] for candidate in incidents
    }
    for log in logs:
        logs_by_incident[log.incident_id].append(log)

    return [
        (candidate, logs_by_incident[candidate.id]) for candidate in incidents
    ]
