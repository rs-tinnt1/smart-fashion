"""
Gallery Controller with MariaDB Integration

Provides gallery page and API endpoints for viewing processed images.
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List
from datetime import datetime
import json

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
    page: int = 1,
    tag: str = None,
    db: DatabaseService = Depends(get_db),
    minio = Depends(get_minio)
):
    """
    Render gallery page with images from database.
    Supports pagination and tag filtering.
    """
    per_page = 10
    offset = (page - 1) * per_page
    
    # Build query based on tag filter
    if tag:
        # Filter by tag
        count_query = """
            SELECT COUNT(DISTINCT i.id) as total
            FROM images i
            INNER JOIN detections d ON d.image_id = i.id
            WHERE d.label = %s
        """
        images_query = """
            SELECT i.id, i.storage_url, i.width, i.height, i.uploaded_at,
                   COUNT(d.id) as detection_count
            FROM images i
            LEFT JOIN detections d ON d.image_id = i.id
            WHERE i.id IN (
                SELECT DISTINCT image_id 
                FROM detections 
                WHERE label = %s
            )
            GROUP BY i.id
            ORDER BY i.uploaded_at DESC
            LIMIT %s OFFSET %s
        """
        count_result = await db.fetch_one(count_query, (tag,))
        total_count = count_result['total'] if count_result else 0
        images_data = await db.fetch_all(images_query, (tag, per_page, offset))
    else:
        # No filter - all images
        count_query = "SELECT COUNT(*) as total FROM images"
        images_query = """
            SELECT i.id, i.storage_url, i.width, i.height, i.uploaded_at,
                   COUNT(d.id) as detection_count
            FROM images i
            LEFT JOIN detections d ON d.image_id = i.id
            GROUP BY i.id
            ORDER BY i.uploaded_at DESC
            LIMIT %s OFFSET %s
        """
        count_result = await db.fetch_one(count_query)
        total_count = count_result['total'] if count_result else 0
        images_data = await db.fetch_all(images_query, (per_page, offset))
    
    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page  # Ceiling division
    
    images = []
    for img in images_data:
        # Get detection labels for this image
        detections = await db.fetch_all(
            "SELECT DISTINCT label FROM detections WHERE image_id = %s",
            (img['id'],)
        )
        class_names = [d['label'] for d in detections]
        
        # Use original image URL (not output)
        original_url = minio.get_public_url(img['storage_url'], request_host=request.headers.get('host'))
        
        images.append({
            "file_id": img['id'],
            "image_url": original_url or f"/static/placeholder.jpg",
            "object_count": img['detection_count'] or 0,
            "classes": class_names,
            "timestamp": img['uploaded_at'].strftime("%Y-%m-%d %H:%M:%S") if img['uploaded_at'] else ""
        })
    
    return templates.TemplateResponse("gallery.html", {
        "request": request,
        "images": images,
        "current_page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "current_tag": tag,
        "per_page": per_page
    })


@router.get("/product/{image_id}", response_class=HTMLResponse)
async def product_detail(
    request: Request,
    image_id: str,
    db: DatabaseService = Depends(get_db),
    minio = Depends(get_minio)
):
    """
    Render product detail page for a specific image.
    Returns original image and detection data with polygons for client-side rendering.
    """
    # Fetch image data
    image = await db.get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Get all detections with polygons for this image
    detections_raw = await db.fetch_all(
        """SELECT d.id, d.label, d.confidence, d.bbox_x, d.bbox_y, d.bbox_w, d.bbox_h,
                  p.points_json, p.simplified
           FROM detections d
           LEFT JOIN polygons p ON p.detection_id = d.id
           WHERE d.image_id = %s""",
        (image_id,)
    )
    
    # Get unique class names
    class_names = list(set([d['label'] for d in detections_raw]))
    object_count = len(detections_raw)
    
    # Format detections data for frontend
    detections_data = []
    for d in detections_raw:
        detection = {
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
        
        # Add polygon data if available
        if d['points_json']:
            detection['polygon'] = {
                "points_json": d['points_json'],
                "simplified": d['simplified']
            }
        
        detections_data.append(detection)
    
    # Get original image URL (not output)
    original_url = minio.get_public_url(image['storage_url'], request_host=request.headers.get('host'))
    
    return templates.TemplateResponse("product-detail.html", {
        "request": request,
        "file_id": image_id,
        "original_url": original_url,
        "image_width": image['width'],
        "image_height": image['height'],
        "object_count": object_count,
        "classes": class_names,
        "detections_json": json.dumps(detections_data),  # JSON string for JavaScript
        "timestamp": image['uploaded_at'].strftime("%Y-%m-%d %H:%M:%S") if image['uploaded_at'] else ""
    })



@router.get("/api/gallery")
async def api_gallery(
    request: Request,
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
        original_url = minio.get_public_url(img['storage_url'], request_host=request.headers.get('host'))
        output_key = f"outputs/{img['id']}_output.jpg"
        output_url = None
        if minio.object_exists(output_key):
            output_url = minio.get_public_url(output_key, request_host=request.headers.get('host'))
        
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
