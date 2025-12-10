"""
Gallery Controller with MariaDB Integration

Provides gallery page and API endpoints for viewing processed images.
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List
from datetime import datetime

from app.services.database import get_database, DatabaseService
from app.services.minio_service import get_minio_service
from app.models.schemas import ImageSummary, DetectionSummary, BBox

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def get_db() -> DatabaseService:
    """Dependency to get database service."""
    return await get_database()


def get_minio():
    """Dependency to get MinIO service."""
    return get_minio_service()


@router.get("/gallery", response_class=HTMLResponse)
async def gallery(
    request: Request,
    db: DatabaseService = Depends(get_db),
    minio = Depends(get_minio)
):
    """
    Render gallery page with images from database.
    """
    # Fetch all images with detection counts
    images_data = await db.fetch_all(
        """SELECT i.id, i.storage_url, i.width, i.height, i.uploaded_at,
                  COUNT(d.id) as detection_count
           FROM images i
           LEFT JOIN detections d ON d.image_id = i.id
           GROUP BY i.id
           ORDER BY i.uploaded_at DESC
           LIMIT 50"""
    )
    
    images = []
    for img in images_data:
        # Get detection labels for this image
        detections = await db.fetch_all(
            "SELECT DISTINCT label FROM detections WHERE image_id = %s",
            (img['id'],)
        )
        class_names = [d['label'] for d in detections]
        
        # Get public URL if available
        output_url = None
        output_key = f"outputs/{img['id']}_output.jpg"
        if minio.object_exists(output_key):
            output_url = minio.get_public_url(output_key)
        else:
            # Fallback to original image
            output_url = minio.get_public_url(img['storage_url'])
        
        images.append({
            "file_id": img['id'],
            "image_url": output_url or f"/static/placeholder.jpg",
            "object_count": img['detection_count'] or 0,
            "classes": class_names,
            "timestamp": img['uploaded_at'].strftime("%Y-%m-%d %H:%M:%S") if img['uploaded_at'] else ""
        })
    
    return templates.TemplateResponse("gallery.html", {"request": request, "images": images})


@router.get("/api/gallery")
async def api_gallery(
    db: DatabaseService = Depends(get_db),
    minio = Depends(get_minio),
    limit: int = 50
):
    """
    API endpoint to get gallery data as JSON.
    """
    # Fetch all images with detection counts
    images_data = await db.fetch_all(
        """SELECT i.id, i.storage_url, i.width, i.height, i.file_size, i.uploaded_at,
                  COUNT(d.id) as detection_count
           FROM images i
           LEFT JOIN detections d ON d.image_id = i.id
           GROUP BY i.id
           ORDER BY i.uploaded_at DESC
           LIMIT %s""",
        (limit,)
    )
    
    result = []
    for img in images_data:
        # Get detections for this image
        detections = await db.fetch_all(
            """SELECT id, label, confidence, bbox_x, bbox_y, bbox_w, bbox_h 
               FROM detections WHERE image_id = %s""",
            (img['id'],)
        )
        
        # Get public URLs
        original_url = minio.get_public_url(img['storage_url'])
        output_key = f"outputs/{img['id']}_output.jpg"
        output_url = None
        if minio.object_exists(output_key):
            output_url = minio.get_public_url(output_key)
        
        result.append({
            "id": img['id'],
            "original_url": original_url,
            "output_url": output_url,
            "width": img['width'],
            "height": img['height'],
            "file_size": img['file_size'],
            "uploaded_at": img['uploaded_at'].isoformat() if img['uploaded_at'] else None,
            "detection_count": img['detection_count'] or 0,
            "detections": [
                {
                    "id": d['id'],
                    "label": d['label'],
                    "confidence": d['confidence'],
                    "bbox": {
                        "x": d['bbox_x'],
                        "y": d['bbox_y'],
                        "w": d['bbox_w'],
                        "h": d['bbox_h']
                    }
                }
                for d in detections
            ]
        })
    
    return {"images": result, "count": len(result)}


@router.get("/api/gallery/{image_id}")
async def api_gallery_image(
    image_id: str,
    db: DatabaseService = Depends(get_db),
    minio = Depends(get_minio)
):
    """
    Get detailed info for a specific image including all detections with polygons.
    """
    image = await db.get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Get all detections with polygons
    detections = await db.fetch_all(
        """SELECT d.id, d.label, d.confidence, d.bbox_x, d.bbox_y, d.bbox_w, d.bbox_h,
                  p.points_json, p.simplified
           FROM detections d
           LEFT JOIN polygons p ON p.detection_id = d.id
           WHERE d.image_id = %s""",
        (image_id,)
    )
    
    # Get URLs
    original_url = minio.get_presigned_url(image['storage_url'])
    output_key = f"outputs/{image_id}_output.jpg"
    output_url = minio.get_presigned_url(output_key) if minio.object_exists(output_key) else None
    
    return {
        "id": image['id'],
        "original_url": original_url,
        "output_url": output_url,
        "width": image['width'],
        "height": image['height'],
        "uploaded_at": image['uploaded_at'].isoformat() if image['uploaded_at'] else None,
        "detections": [
            {
                "id": d['id'],
                "label": d['label'],
                "confidence": d['confidence'],
                "bbox": {
                    "x": d['bbox_x'],
                    "y": d['bbox_y'],
                    "w": d['bbox_w'],
                    "h": d['bbox_h']
                },
                "polygon": d['points_json'] if d['points_json'] else None
            }
            for d in detections
        ]
    }
