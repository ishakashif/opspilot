from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.incident import Incident
from app.models.log import Log
from app.schemas.log import LogCreate, LogResponse

router = APIRouter(prefix="/incidents/{incident_id}/logs", tags=["Logs"])


@router.post(
    "/",
    response_model=LogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_log(
    incident_id: int,
    log_in: LogCreate,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    log = Log(
        incident_id=incident_id,
        level=log_in.level,
        message=log_in.message,
        source=log_in.source,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/", response_model=list[LogResponse])
def list_logs(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    return (
        db.query(Log)
        .filter(Log.incident_id == incident_id)
        .order_by(Log.timestamp.asc())
        .all()
    )
