"""
Image Schemas

Pydantic models for image metadata and responses.
"""

from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.models.detection_schema import DetectionSummary


class ImageSummary(BaseModel):
    """Image metadata summary."""
    id: str
    storage_url: str
    width: int
    height: int
    file_size: int
    uploaded_at: datetime


class ImageResponse(BaseModel):
    """Image with detections."""
    id: str
    storage_url: str
    width: int
    height: int
    file_size: int
    uploaded_at: datetime
    detections: List[DetectionSummary] = []
