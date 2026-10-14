import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes.analysis import router as analysis_router
from app.routes.auth import router as auth_router
from app.routes.incidents import router as incidents_router 
from app.routes.logs import router as logs_router
from app.routes.similar_incidents import router as similar_incidents_router


logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpsPilot API",
    description="Backend API for the OpsPilot incident management platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    del request
    detail = [
        {
            "loc": error.get("loc", ()),
            "msg": error.get("msg", "Invalid request"),
            "type": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled %s on %s",
        type(exc).__name__,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

app.include_router(auth_router)
app.include_router(incidents_router)
app.include_router(logs_router)
app.include_router(analysis_router)
app.include_router(similar_incidents_router)

@app.get("/health")
def health_check():
    return{"status": "healthy"}
