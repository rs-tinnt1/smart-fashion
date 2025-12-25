"""
Models Package

Contains Pydantic schemas for API request/response validation.
Organized by domain: detection, image, job, upload, health.
"""

# Detection schemas
from app.models.detection_schema import (
    BBox,
    PolygonPoint,
    PolygonData,
    DetectionSummary,
    DetectionDetail,
)

# Image schemas
from app.models.image_schema import (
    ImageSummary,
    ImageResponse,
)

# Upload schemas
from app.models.upload_schema import UploadResponse

# Job schemas
from app.models.job_schema import JobStatus

# Health schemas
from app.models.health_schema import HealthResponse

__all__ = [
    # Detection
    "BBox",
    "PolygonPoint",
    "PolygonData",
    "DetectionSummary",
    "DetectionDetail",
    # Image
    "ImageSummary",
    "ImageResponse",
    # Upload
    "UploadResponse",
    # Job
    "JobStatus",
    # Health
    "HealthResponse",
]
