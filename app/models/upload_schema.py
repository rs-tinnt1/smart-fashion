"""
Upload Schemas

Pydantic models for file upload responses.
"""

from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response from upload endpoint."""
    job_id: str
    image_id: str
    status: str = "queued"
