"""
Services Package

Contains business logic and infrastructure services.
"""

# Database service
from app.services.database_service import get_database, close_database, DatabaseService

# Storage service (S3/R2)
from app.services.storage_service import get_storage_service, StorageService

# Segmentation service
from app.services.segmentation_service import segment_one_file, delete_output, get_stats

# Inference service (YOLO)
from app.services.inference_service import YOLOSegmentation

__all__ = [
    # Database
    "get_database",
    "close_database",
    "DatabaseService",
    # Storage
    "get_storage_service",
    "StorageService",
    # Segmentation
    "segment_one_file",
    "delete_output",
    "get_stats",
    # Inference
    "YOLOSegmentation",
]
