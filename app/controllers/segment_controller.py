from datetime import datetime
from threading import Lock
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.config import MODEL_PRELOAD
from app.services.database_service import get_database
from app.services.runtime_status import add_runtime_warning, get_runtime_snapshot, set_runtime_component
from app.services.segmentation_service import delete_output, get_stats, segment_one_file

router = APIRouter()

model = None  # Will be injected by main.py
model_name = None  # Will be injected by main.py
storage_service = None  # Will be injected by main.py
model_lock = Lock()


def _load_model_on_demand(request: Request | None = None) -> Any:
    global model, model_name

    if model is not None:
        if request is not None and model_name is not None:
            set_runtime_component(request.app, "model", True, f"loaded: {model_name}")
        return model

    if storage_service is None:
        if request is not None:
            set_runtime_component(request.app, "storage", False, "storage service not initialized")
        raise HTTPException(status_code=503, detail="Storage service not initialized")

    with model_lock:
        if model is not None:
            return model

        try:
            from app.services.inference_service import load_best_segment_model

            model, model_name = load_best_segment_model(storage_service)
            if request is not None and model_name is not None:
                set_runtime_component(request.app, "model", True, f"loaded on demand: {model_name}")
            return model
        except Exception as exc:
            if request is not None:
                set_runtime_component(request.app, "model", False, str(exc))
                add_runtime_warning(request.app, f"On-demand model load failed: {exc}")
            raise HTTPException(status_code=503, detail=f"Model failed to initialize: {exc}") from exc


def get_model(request: Request):
    return _load_model_on_demand(request)


def get_storage():
    global storage_service
    if storage_service is None:
        raise HTTPException(status_code=503, detail="Storage service not initialized")
    return storage_service


async def _get_optional_db(request: Request) -> Any | None:
    try:
        db = await get_database()
        set_runtime_component(request.app, "database", True, "connection pool initialized")
        return db
    except Exception as exc:
        set_runtime_component(request.app, "database", False, str(exc))
        add_runtime_warning(request.app, f"Database initialization failed: {exc}")
        return None


def _build_detection_record(obj: dict[str, Any]) -> dict[str, Any]:
    bbox = obj.get("bbox") or {}
    contours = obj.get("contours", [])

    bbox_x = int(bbox.get("x", 0))
    bbox_y = int(bbox.get("y", 0))
    bbox_w = int(bbox.get("w", 0))
    bbox_h = int(bbox.get("h", 0))

    if (bbox_w <= 0 or bbox_h <= 0) and contours and contours[0]:
        xs = [point["x"] for point in contours[0]]
        ys = [point["y"] for point in contours[0]]
        bbox_x = min(xs)
        bbox_y = min(ys)
        bbox_w = max(xs) - bbox_x
        bbox_h = max(ys) - bbox_y

    return {
        "label": obj.get("class_name", "unknown"),
        "confidence": float(obj.get("confidence", 0.0)),
        "bbox_x": bbox_x,
        "bbox_y": bbox_y,
        "bbox_w": bbox_w,
        "bbox_h": bbox_h,
        "contours": contours,
        "simplified": True,
        "embedding": {"model_name": "placeholder", "vector": [0.0] * 128},
    }


UploadedFiles = Annotated[list[UploadFile], File(...)]
LoadedModel = Annotated[Any, Depends(get_model)]
StorageDependency = Annotated[Any, Depends(get_storage)]


@router.get("/api/health")
async def health_check(request: Request):
    startup_status, startup_warnings = get_runtime_snapshot(request.app)
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_name": model_name,
        "startup": startup_status,
        "warnings": startup_warnings,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/api/healthz")
async def liveness_check(request: Request):
    _, startup_warnings = get_runtime_snapshot(request.app)
    return {
        "status": "ok",
        "warnings": len(startup_warnings),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/api/readyz")
async def readiness_check(request: Request):
    checks: dict[str, dict[str, str | bool]] = {}

    if storage_service is None:
        checks["storage"] = {"ready": False, "detail": "storage service not initialized"}
        set_runtime_component(request.app, "storage", False, "storage service not initialized")
    else:
        try:
            bucket_ready = await run_in_threadpool(storage_service.ensure_bucket_exists)
            storage_detail = "bucket reachable" if bucket_ready else "bucket not reachable"
            checks["storage"] = {"ready": bucket_ready, "detail": storage_detail}
            set_runtime_component(request.app, "storage", bucket_ready, storage_detail)
        except Exception as exc:
            checks["storage"] = {"ready": False, "detail": str(exc)}
            set_runtime_component(request.app, "storage", False, str(exc))

    try:
        db = await get_database()
        db_probe = await db.fetch_one("SELECT 1 AS ok")
        database_ready = db_probe is not None and db_probe.get("ok") == 1
        database_detail = "query succeeded" if database_ready else "query returned no result"
        checks["database"] = {"ready": database_ready, "detail": database_detail}
        set_runtime_component(request.app, "database", database_ready, database_detail)
    except Exception as exc:
        checks["database"] = {"ready": False, "detail": f"optional for free profile: {exc}"}
        set_runtime_component(request.app, "database", False, str(exc))

    if model is not None:
        model_detail = f"loaded: {model_name}" if model_name else "loaded"
        checks["model"] = {"ready": True, "detail": model_detail}
        set_runtime_component(request.app, "model", True, model_detail)
    elif MODEL_PRELOAD:
        checks["model"] = {"ready": False, "detail": "MODEL_PRELOAD=true but model is not loaded"}
        set_runtime_component(request.app, "model", False, "MODEL_PRELOAD=true but model is not loaded")
    else:
        checks["model"] = {"ready": True, "detail": "lazy load enabled; first segmentation request will warm the model"}
        set_runtime_component(request.app, "model", False, "deferred until first segmentation request")

    required_components = ["storage", "model"] if MODEL_PRELOAD else ["storage"]
    ready = all(bool(checks[component]["ready"]) for component in required_components if component in checks)
    response = {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }
    return JSONResponse(status_code=200 if ready else 503, content=response)


@router.post("/api/segment")
async def segment_clothing(
    request: Request,
    files: UploadedFiles,
    yolo_model: LoadedModel,
    storage: StorageDependency,
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    results = []

    # File size limit
    max_file_size_kb = 500
    max_file_size_bytes = max_file_size_kb * 1024
    filename = "upload.jpg"
    db = await _get_optional_db(request)

    for file in files:
        filename = file.filename if file.filename is not None else "upload.jpg"
        try:
            # Check file size before processing
            content_type = file.content_type if file.content_type is not None else "application/octet-stream"
            content = await file.read()
            file_size = len(content)
            if file_size > max_file_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {filename} size ({file_size // 1024}KB) exceeds maximum allowed ({max_file_size_kb}KB)",
                )
            # Process image with YOLO model using memory buffer
            result = await run_in_threadpool(
                segment_one_file,
                content,
                filename,
                content_type,
                yolo_model,
                storage,
                request.headers.get("host"),
            )

            if db is not None:
                try:
                    segmentation_data = result.get("segmentation_data", {})
                    objects = segmentation_data.get("objects", [])
                    detection_records = [_build_detection_record(obj) for obj in objects]
                    storage_key = result.get("original_image_key")

                    if storage_key:
                        await db.create_image_with_detections(
                            image_id=result["file_id"],
                            storage_url=storage_key,
                            width=segmentation_data.get("image_width", 0),
                            height=segmentation_data.get("image_height", 0),
                            file_size=file_size,
                            hash=None,
                            detections=detection_records,
                        )
                    else:
                        add_runtime_warning(
                            request.app,
                            f"Skipped database persistence for {filename}: original image key unavailable",
                        )
                except Exception as exc:
                    add_runtime_warning(request.app, f"Database persistence failed for {filename}: {exc}")

            results.append(result)
        except HTTPException:
            # Let HTTPException propagate (e.g., file size validation)
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing {filename}: {str(e)}") from e

    return {"success": True, "processed_images": len(results), "results": results}


@router.delete("/api/delete/{file_id}")
async def delete_output_endpoint(file_id: str, storage: StorageDependency):
    image = None
    db = None

    try:
        db = await get_database()
        image = await db.fetch_one("SELECT storage_url FROM images WHERE id = %s", (file_id,))
    except Exception:
        image = None

    deleted = delete_output(file_id, storage, image_storage_url=image["storage_url"] if image else None)

    if image and db is not None:
        await db.execute("DELETE FROM images WHERE id = %s", (file_id,))
        deleted.append("db_record")

    if not deleted:
        raise HTTPException(status_code=404, detail="Files not found")
    return {"success": True, "deleted": deleted}


@router.get("/api/stats")
async def get_stats_endpoint():
    return get_stats()
