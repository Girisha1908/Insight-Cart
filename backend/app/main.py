"""InsightCart FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title="InsightCart API",
    description="E-commerce decision intelligence platform",
    version="0.1.0",
)

# Allow the local Vite dev server (and any local origin) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/api/health", tags=["system"])
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}
