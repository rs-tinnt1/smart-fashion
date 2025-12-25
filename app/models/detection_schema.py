"""
Detection and Segmentation Schemas

Pydantic models for detection, bounding boxes, and polygon data.
"""

from pydantic import BaseModel
from typing import List, Optional


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
