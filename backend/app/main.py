from fastapi import FastAPI

app = FastAPI(
    title="OpsPilot API",
    description="Backend API for the OpsPilot incident management platform",
    version="0.1.0",
)
"""
we're telling FastAPI: when someone sends an HTTP GET request to /health,
execure the function directly underneath it.
"""
@app.get("/health")
def health_check():
    return{"status": "healthy"}
