from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from app.services.api import segment_one_file, delete_output, get_stats
from app.services.database import get_database, DatabaseService
from typing import List
from datetime import datetime
import uuid
import json

router = APIRouter()

model = None  # Will be injected by main.py
minio_service = None  # Will be injected by main.py


def get_model():
    global model
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return model


def get_minio():
    global minio_service
    if minio_service is None:
        raise HTTPException(status_code=503, detail="MinIO service not initialized")
    return minio_service


async def get_db() -> DatabaseService:
    """Dependency to get database service."""
    return await get_database()


@router.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/api/segment")
async def segment_clothing(
    request: Request,
    files: List[UploadFile] = File(...),
    yolo_model=Depends(get_model),
    minio=Depends(get_minio),
    db: DatabaseService = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    base_url = str(request.base_url).rstrip("/")
    results = []
    
    # File size limit
    MAX_FILE_SIZE_KB = 500
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_KB * 1024
    
    for file in files:
        try:
            # Check file size before processing
            content = await file.read()
            file_size = len(content)
            if file_size > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} size ({file_size // 1024}KB) exceeds maximum allowed ({MAX_FILE_SIZE_KB}KB)"
                )
            # Reset file position for segment_one_file
            await file.seek(0)
            
            # Process image with ONNX model
            result = segment_one_file(file, yolo_model, minio, base_url)
            
            # Save to database
            image_id = result["file_id"]
            segmentation_data = result.get("segmentation_data", {})
            objects = segmentation_data.get("objects", [])
            
            # Create image record in database
            # Use output image URL as storage_url
            storage_key = f"outputs/{image_id}_output.jpg"
            await db.create_image(
                image_id=image_id,
                storage_url=storage_key,
                width=segmentation_data.get("image_width", 0),
                height=segmentation_data.get("image_height", 0),
                file_size=0,
                hash=None
            )
            
            # Save each detection
            for obj in objects:
                # Get bounding box from contours if available
                bbox_x, bbox_y, bbox_w, bbox_h = 0, 0, 0, 0
                contours = obj.get("contours", [])
                if contours and len(contours) > 0 and len(contours[0]) > 0:
                    # Calculate bounding box from contour points
                    all_points = contours[0]
                    if all_points:
                        xs = [p["x"] for p in all_points]
                        ys = [p["y"] for p in all_points]
                        bbox_x = min(xs)
                        bbox_y = min(ys)
                        bbox_w = max(xs) - bbox_x
                        bbox_h = max(ys) - bbox_y
                
                # Create detection record
                detection_id = await db.create_detection(
                    image_id=image_id,
                    label=obj.get("class_name", "unknown"),
                    confidence=obj.get("confidence", 0.0),
                    bbox_x=bbox_x,
                    bbox_y=bbox_y,
                    bbox_w=bbox_w,
                    bbox_h=bbox_h
                )
                
                # Create polygon record if contours exist
                if contours:
                    await db.create_polygon(
                        detection_id=detection_id,
                        points_json=json.dumps(contours),
                        simplified=True
                    )
                
                # Create stub embedding (placeholder)
                embedding_vector = [0.0] * 128
                await db.create_embedding(
                    detection_id=detection_id,
                    model_name="placeholder",
                    vector=json.dumps(embedding_vector)
                )
            
            results.append(result)
        except HTTPException:
            # Let HTTPException propagate (e.g., file size validation)
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")
    
    return {"success": True, "processed_images": len(results), "results": results}


@router.delete("/api/outputs/{file_id}")
async def delete_output_endpoint(file_id: str, minio=Depends(get_minio)):
    deleted = delete_output(file_id, minio)
    if not deleted:
        raise HTTPException(status_code=404, detail="Files not found")
    return {"success": True, "deleted": deleted}


@router.get("/api/stats")
async def get_stats_endpoint():
    return get_stats()
