"""
Image Schemas

Pydantic models for image metadata and responses.
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.detection_schema import DetectionSummary


class ImageResponse(BaseModel):
    """Image with detections."""

    id: str
    storage_url: str
    width: int
    height: int
    file_size: int
    uploaded_at: datetime
    detections: list[DetectionSummary] = []
