from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user, require_engineer
from app.models.incident import Incident
from app.models.log import Log
from app.schemas.log import LogBulkCreate, LogCreate, LogResponse

router = APIRouter(prefix="/incidents/{incident_id}/logs", tags=["Logs"])


@router.post(
    "/",
    response_model=LogResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_engineer)],
)
def create_log(
    incident_id: int,
    log_in: LogCreate,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident Not Found")

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


@router.post(
    "/bulk",
    response_model=list[LogResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_engineer)],
)
def create_logs_bulk(
    incident_id: int,
    log_bulk: LogBulkCreate,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    logs = []
    for log_in in log_bulk.logs:
        log = Log(
            incident_id=incident_id,
            level=log_in.level,
            message=log_in.message,
            source=log_in.source,
        )
        logs.append(log)

    db.add_all(logs)
    db.commit()
    for log in logs:
        db.refresh(log)
    return logs


@router.get(
    "/",
    response_model=list[LogResponse],
    dependencies=[Depends(get_current_user)],
)
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
