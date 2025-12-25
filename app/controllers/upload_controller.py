"""
Upload Controller for Smart Fashion API

Handles image upload, job creation, and retrieval endpoints.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional
import uuid
import hashlib
import json
from pathlib import Path
from datetime import datetime

from app.models.upload_schema import UploadResponse
from app.models.image_schema import ImageResponse
from app.models.detection_schema import DetectionDetail, DetectionSummary, BBox, PolygonData, PolygonPoint
from app.models.job_schema import JobStatus
from app.services.database_service import get_database, DatabaseService
from app.services.storage_service import get_minio_service

router = APIRouter(tags=["upload"])


async def get_db() -> DatabaseService:
    """Dependency to get database service."""
    return await get_database()


def get_minio():
    """Dependency to get MinIO service."""
    minio = get_minio_service()
    if minio is None:
        raise HTTPException(status_code=503, detail="MinIO service not initialized")
    return minio


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: DatabaseService = Depends(get_db),
    minio = Depends(get_minio)
):
    """
    Upload an image for processing.
    
    - Stores the image in MinIO
    - Creates image record in database
    - Creates a pending job for processing
    - Returns immediately with job_id and image_id
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate IDs
    image_id = str(uuid.uuid4())
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file size (max 500KB)
    MAX_FILE_SIZE_KB = 500
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_KB * 1024
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400, 
            detail=f"File size ({file_size // 1024}KB) exceeds maximum allowed ({MAX_FILE_SIZE_KB}KB)"
        )
    
    # Calculate hash
    file_hash = hashlib.sha256(content).hexdigest()[:32]
    
    # Determine storage key
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    storage_key = f"uploads/{image_id}{ext}"
    
    # Upload to MinIO
    if not minio.upload_bytes(content, storage_key, content_type=file.content_type):
        raise HTTPException(status_code=500, detail="Failed to upload file to storage")
    
    # Get image dimensions (optional, will be updated by worker)
    width, height = 0, 0
    try:
        import cv2
        import numpy as np
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            height, width = img.shape[:2]
    except Exception:
        pass  # Dimensions will be 0, worker can update later
    
    # Create image record
    storage_url = storage_key
    await db.create_image(
        image_id=image_id,
        storage_url=storage_url,
        width=width,
        height=height,
        file_size=file_size,
        hash=file_hash
    )
    
    # Create pending job
    job_id = await db.create_job(image_id)
    
    return UploadResponse(
        job_id=job_id,
        image_id=image_id,
        status="queued"
    )


@router.get("/images/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: str,
    db: DatabaseService = Depends(get_db),
    minio = Depends(get_minio)
):
    """
    Get image metadata and detections summary.
    """
    image = await db.get_image_with_detections(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Build response
    detections = []
    for det in image.get('detections', []):
        detections.append(DetectionSummary(
            id=det['id'],
            label=det['label'],
            confidence=det['confidence'],
            bbox=BBox(
                x=det['bbox_x'],
                y=det['bbox_y'],
                w=det['bbox_w'],
                h=det['bbox_h']
            )
        ))
    
    # Get presigned URL for storage
    storage_url = minio.get_presigned_url(image['storage_url']) or image['storage_url']
    
    return ImageResponse(
        id=image['id'],
        storage_url=storage_url,
        width=image['width'],
        height=image['height'],
        file_size=image['file_size'],
        uploaded_at=image['uploaded_at'],
        detections=detections
    )


@router.get("/detections/{detection_id}", response_model=DetectionDetail)
async def get_detection(
    detection_id: str,
    db: DatabaseService = Depends(get_db)
):
    """
    Get full detection data including polygon and embedding.
    """
    detection = await db.get_detection(detection_id)
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    
    # Build polygon data
    polygon_data = None
    if detection.get('polygon') and detection['polygon'].get('points_json'):
        try:
            points_raw = detection['polygon']['points_json']
            if isinstance(points_raw, str):
                points_raw = json.loads(points_raw)
            
            # Convert to nested list of PolygonPoint
            points_list = []
            for contour in points_raw:
                contour_points = [PolygonPoint(x=p['x'], y=p['y']) for p in contour]
                points_list.append(contour_points)
            
            polygon_data = PolygonData(
                points=points_list,
                simplified=detection['polygon'].get('simplified', False)
            )
        except Exception:
            pass
    
    # Build embedding (truncate to first 10 values for response)
    embedding = None
    if detection.get('embedding') and detection['embedding'].get('vector'):
        try:
            vector = detection['embedding']['vector']
            if isinstance(vector, str):
                vector = json.loads(vector)
            embedding = vector[:10] if len(vector) > 10 else vector
        except Exception:
            pass
    
    return DetectionDetail(
        id=detection['id'],
        image_id=detection['image_id'],
        label=detection['label'],
        confidence=detection['confidence'],
        bbox=BBox(
            x=detection['bbox_x'],
            y=detection['bbox_y'],
            w=detection['bbox_w'],
            h=detection['bbox_h']
        ),
        polygon=polygon_data,
        embedding=embedding
    )


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    db: DatabaseService = Depends(get_db)
):
    """
    Get job processing status.
    """
    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(
        id=job['id'],
        image_id=job['image_id'],
        status=job['status'],
        error_message=job.get('error_message'),
        created_at=job['created_at'],
        started_at=job.get('started_at'),
        completed_at=job.get('completed_at')
    )
