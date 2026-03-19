import json
from datetime import datetime
from threading import Lock
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.services.database_service import DatabaseService, get_database
from app.services.segmentation_service import delete_output, get_stats, segment_one_file

router = APIRouter()

model = None  # Will be injected by main.py
model_name = None  # Will be injected by main.py
storage_service = None  # Will be injected by main.py
model_lock = Lock()


def _load_model_on_demand() -> Any:
    global model, model_name

    if model is not None:
        return model

    if storage_service is None:
        raise HTTPException(status_code=503, detail="Storage service not initialized")

    with model_lock:
        if model is not None:
            return model

        try:
            from app.services.inference_service import load_best_segment_model

            model, model_name = load_best_segment_model(storage_service)
            return model
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Model failed to initialize: {exc}") from exc


def get_model():
    return _load_model_on_demand()


def get_storage():
    global storage_service
    if storage_service is None:
        raise HTTPException(status_code=503, detail="Storage service not initialized")
    return storage_service


async def get_db() -> DatabaseService:
    """Dependency to get database service."""
    return await get_database()


UploadedFiles = Annotated[list[UploadFile], File(...)]
LoadedModel = Annotated[Any, Depends(get_model)]
StorageDependency = Annotated[Any, Depends(get_storage)]
DatabaseDependency = Annotated[DatabaseService, Depends(get_db)]


@router.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_name": model_name,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/api/segment")
async def segment_clothing(
    request: Request,
    files: UploadedFiles,
    yolo_model: LoadedModel,
    storage: StorageDependency,
    db: DatabaseDependency,
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    base_url = str(request.base_url).rstrip("/")
    results = []

    # File size limit
    max_file_size_kb = 500
    max_file_size_bytes = max_file_size_kb * 1024

    for file in files:
        try:
            # Check file size before processing
            content = await file.read()
            file_size = len(content)
            if file_size > max_file_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} size ({file_size // 1024}KB) exceeds maximum allowed ({max_file_size_kb}KB)",
                )
            # Process image with YOLO model using memory buffer
            result = segment_one_file(
                image_bytes=content,
                filename=file.filename,
                content_type=file.content_type,
                model=yolo_model,
                storage_service=storage,
                base_url=base_url,
                request_host=request.headers.get("host")
            )

            # Save to database
            image_id = result["file_id"]
            segmentation_data = result.get("segmentation_data", {})
            objects = segmentation_data.get("objects", [])

            # Create image record in database
            # Use original image key (not output image)
            storage_key = result.get("original_image_key", f"images/{image_id}.jpg")
            await db.create_image(
                image_id=image_id,
                storage_url=storage_key,
                width=segmentation_data.get("image_width", 0),
                height=segmentation_data.get("image_height", 0),
                file_size=file_size,
                hash=None,
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
                    bbox_h=bbox_h,
                )

                # Create polygon record if contours exist
                if contours:
                    await db.create_polygon(
                        detection_id=detection_id, points_json=json.dumps(contours), simplified=True
                    )

                # Create stub embedding (placeholder)
                embedding_vector = [0.0] * 128
                await db.create_embedding(
                    detection_id=detection_id, model_name="placeholder", vector=json.dumps(embedding_vector)
                )

            results.append(result)
        except HTTPException:
            # Let HTTPException propagate (e.g., file size validation)
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}") from e

    return {"success": True, "processed_images": len(results), "results": results}


@router.delete("/api/delete/{file_id}")
async def delete_output_endpoint(file_id: str, storage: StorageDependency, db: DatabaseDependency):
    image = await db.fetch_one("SELECT storage_url FROM images WHERE id = %s", (file_id,))
    
    deleted = delete_output(file_id, storage, image_storage_url=image['storage_url'] if image else None)
    
    if image:
        await db.execute("DELETE FROM images WHERE id = %s", (file_id,))
        deleted.append("db_record")
        
    if not deleted:
        raise HTTPException(status_code=404, detail="Files not found")
    return {"success": True, "deleted": deleted}


@router.get("/api/stats")
async def get_stats_endpoint():
    return get_stats()
