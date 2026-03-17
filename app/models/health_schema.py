"""
Health Check Schemas

Pydantic models for health check endpoints.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model_loaded: bool
    model_name: str | None = None
    database_connected: bool
    timestamp: str
