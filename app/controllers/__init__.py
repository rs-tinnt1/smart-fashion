"""
Controllers Package

Contains FastAPI routers for handling HTTP requests.
Organized by feature: segmentation, gallery, upload.
"""

from app.controllers.segment_controller import router as segment_router
from app.controllers.gallery_controller import router as gallery_router
from app.controllers.upload_controller import router as upload_router

__all__ = [
    "segment_router",
    "gallery_router",
    "upload_router",
]
