"""
Job Schemas

Pydantic models for async job processing.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobStatus(BaseModel):
    """Job status response."""
    id: str
    image_id: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
