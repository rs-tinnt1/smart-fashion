"""
Pydantic Models for Smart Fashion API

Request/response validation schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BBox(BaseModel):
    """Bounding box coordinates."""
    x: int
    y: int
    w: int
    h: int


class PolygonPoint(BaseModel):
    """A single point in a polygon."""
    x: int
    y: int


class PolygonData(BaseModel):
    """Polygon data for a detection."""
    points: List[List[PolygonPoint]]  # Nested list for multiple contours
    simplified: bool = False


class DetectionSummary(BaseModel):
    """Summary of a detection (for image listing)."""
    id: str
    label: str
    confidence: float
    bbox: BBox


class DetectionDetail(BaseModel):
    """Full detection data including polygon and embedding."""
    id: str
    image_id: str
    label: str
    confidence: float
    bbox: BBox
    polygon: Optional[PolygonData] = None
    embedding: Optional[List[float]] = None  # Truncated for response


class UploadResponse(BaseModel):
    """Response from upload endpoint."""
    job_id: str
    image_id: str
    status: str = "queued"


class JobStatus(BaseModel):
    """Job status response."""
    id: str
    image_id: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


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


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    database_connected: bool
    timestamp: str
