from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import Base, engine
from app.models.incident import Incident
from app.models.log import Log
from app.routes.incidents import router as incidents_router 
from app.routes.logs import router as logs_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OpsPilot API",
    description="Backend API for the OpsPilot incident management platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents_router)
app.include_router(logs_router)
"""
we're telling FastAPI: when someone sends an HTTP GET request to /health,
execure the function directly underneath it.
"""
@app.get("/health")
def health_check():
    return{"status": "healthy"}
