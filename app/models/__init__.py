"""
Models Package

Contains Pydantic schemas for API request/response validation.
Organized by domain: detection, image, job, upload.
"""

# Detection schemas
from app.models.detection_schema import BBox, DetectionDetail, DetectionSummary, PolygonData, PolygonPoint

# Image schemas
from app.models.image_schema import ImageResponse

# Job schemas
from app.models.job_schema import JobStatus

# Upload schemas
from app.models.upload_schema import UploadResponse

__all__ = [
    # Detection
    "BBox",
    "PolygonPoint",
    "PolygonData",
    "DetectionSummary",
    "DetectionDetail",
    # Image
    "ImageResponse",
    # Upload
    "UploadResponse",
    # Job
    "JobStatus",
]
