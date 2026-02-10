"""
Main module - FastAPI application entry point.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Nick RAG API",
    description="RAG service API",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for liveness/readiness probes."""
    return {"status": "ok", "message": "service is running"}
