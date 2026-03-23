"""
Gallery Controller with MySQL-Compatible Integration

Provides gallery page and API endpoints for viewing processed images.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Annotated, Any

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.services.database_service import DatabaseService, get_database
from app.services.runtime_status import add_runtime_warning, set_runtime_component
from app.services.storage_service import get_storage_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")

MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

OVERLAY_PALETTE = [
    "#F25F5C",
    "#247BA0",
    "#70C1B3",
    "#FF9F1C",
    "#7F5AF0",
    "#2A9D8F",
    "#E76F51",
    "#3A86FF",
    "#EF476F",
    "#6A994E",
]


async def get_db(request: Request) -> DatabaseService | None:
    """Dependency to get database service."""
    try:
        db = await get_database()
        set_runtime_component(request.app, "database", True, "connection pool initialized")
        return db
    except Exception as exc:
        set_runtime_component(request.app, "database", False, str(exc))
        add_runtime_warning(request.app, f"Database initialization failed: {exc}")
        return None


def get_storage():
    """Dependency to get storage service."""
    return get_storage_service()


def _get_media_type_from_key(storage_key: str) -> str:
    return MEDIA_TYPES.get(Path(storage_key).suffix.lower(), "application/octet-stream")


def _parse_polygon_points(points_json: Any) -> list[list[dict[str, int]]]:
    if not points_json:
        return []
    if isinstance(points_json, str):
        try:
            parsed = json.loads(points_json)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return points_json if isinstance(points_json, list) else []


def _build_polygon_crop(image_bytes: bytes, detection: dict[str, Any]) -> bytes | None:
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        return None

    polygon = detection.get("polygon")
    polygon_points = _parse_polygon_points(polygon.get("points_json") if isinstance(polygon, dict) else None)
    if polygon_points:
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        all_points: list[np.ndarray] = []

        for contour in polygon_points:
            if not contour:
                continue
            contour_array = np.array([[point["x"], point["y"]] for point in contour], dtype=np.int32)
            if contour_array.size == 0:
                continue
            all_points.append(contour_array)
            cv2.fillPoly(mask, [contour_array], 255)

        if not all_points:
            polygon_points = []
        else:
            stacked_points = np.vstack(all_points)
            x, y, w, h = cv2.boundingRect(stacked_points)
            masked = cv2.bitwise_and(image, image, mask=mask)
            cropped = masked[y : y + h, x : x + w]
            alpha = mask[y : y + h, x : x + w]
            rgba = cv2.cvtColor(cropped, cv2.COLOR_BGR2BGRA)
            rgba[:, :, 3] = alpha
            ok, encoded = cv2.imencode(".png", rgba)
            return encoded.tobytes() if ok else None

    bbox = detection.get("bbox")
    if isinstance(bbox, dict):
        x = int(bbox.get("x", 0))
        y = int(bbox.get("y", 0))
        w = int(bbox.get("w", 0))
        h = int(bbox.get("h", 0))
    else:
        x = int(detection.get("bbox_x", 0))
        y = int(detection.get("bbox_y", 0))
        w = int(detection.get("bbox_w", 0))
        h = int(detection.get("bbox_h", 0))
    if w <= 0 or h <= 0:
        return None
    cropped = image[y : y + h, x : x + w]
    ok, encoded = cv2.imencode(".png", cropped)
    return encoded.tobytes() if ok else None


def _build_in_clause(values: list[str]) -> tuple[str, tuple[str, ...]]:
    placeholders = ", ".join(["%s"] * len(values))
    return placeholders, tuple(values)


async def _fetch_labels_by_image(db: DatabaseService, image_ids: list[str]) -> dict[str, list[str]]:
    if not image_ids:
        return {}

    placeholders, params = _build_in_clause(image_ids)
    rows = await db.fetch_all(
        f"SELECT image_id, label FROM detections WHERE image_id IN ({placeholders}) GROUP BY image_id, label ORDER BY label",
        params,
    )

    labels_by_image: dict[str, list[str]] = {image_id: [] for image_id in image_ids}
    for row in rows:
        labels_by_image.setdefault(row["image_id"], []).append(row["label"])
    return labels_by_image


async def _fetch_detections_by_image(db: DatabaseService, image_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not image_ids:
        return {}

    placeholders, params = _build_in_clause(image_ids)
    rows = await db.fetch_all(
        f"""SELECT id, image_id, label, confidence, bbox_x, bbox_y, bbox_w, bbox_h
             FROM detections
             WHERE image_id IN ({placeholders})
             ORDER BY image_id, confidence DESC""",
        params,
    )

    detections_by_image: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        detections_by_image[row["image_id"]].append(row)
    return dict(detections_by_image)


DatabaseDependency = Annotated[DatabaseService | None, Depends(get_db)]
StorageDependency = Annotated[Any, Depends(get_storage)]


@router.get("/gallery", response_class=HTMLResponse)
async def gallery(
    request: Request,
    db: DatabaseDependency,
    storage: StorageDependency,
    page: int = 1,
    tag: str | None = None,
):
    """
    Render gallery page with images from database.
    Supports pagination and tag filtering.
    """
    per_page = 10
    offset = (page - 1) * per_page

    if db is None:
        return templates.TemplateResponse(
            "pages/gallery.html",
            {
                "request": request,
                "images": [],
                "current_page": page,
                "total_pages": 0,
                "total_count": 0,
                "current_tag": tag,
                "per_page": per_page,
            },
        )

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
        total_count = count_result["total"] if count_result else 0
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
        total_count = count_result["total"] if count_result else 0
        images_data = await db.fetch_all(images_query, (per_page, offset))

    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page  # Ceiling division

    image_ids = [img["id"] for img in images_data]
    labels_by_image = await _fetch_labels_by_image(db, image_ids)

    images = []
    for img in images_data:
        class_names = labels_by_image.get(img["id"], [])

        # Use original image URL (not output)
        original_url = storage.get_public_url(img["storage_url"], request_host=request.headers.get("host"))

        images.append(
            {
                "file_id": img["id"],
                "image_url": original_url or "/static/placeholder.jpg",
                "object_count": img["detection_count"] or 0,
                "classes": class_names,
                "timestamp": img["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S") if img["uploaded_at"] else "",
            }
        )

    return templates.TemplateResponse(
        "pages/gallery.html",
        {
            "request": request,
            "images": images,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "current_tag": tag,
            "per_page": per_page,
        },
    )


@router.get("/product/{image_id}", response_class=HTMLResponse)
async def product_detail(
    request: Request,
    image_id: str,
    db: DatabaseDependency,
    storage: StorageDependency,
):
    """
    Render product detail page for a specific image.
    Returns original image and detection data with polygons for client-side rendering.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Gallery is unavailable on the free profile")

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
           WHERE d.image_id = %s
           ORDER BY d.confidence DESC, d.id ASC""",
        (image_id,),
    )

    # Get unique class names
    class_names = list({d["label"] for d in detections_raw})
    object_count = len(detections_raw)

    # Format detections data for frontend
    detections_data = []
    grouped_detections: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for index, d in enumerate(detections_raw):
        overlay_color = OVERLAY_PALETTE[index % len(OVERLAY_PALETTE)]
        detection = {
            "id": d["id"],
            "label": d["label"],
            "confidence": d["confidence"],
            "bbox": {"x": d["bbox_x"], "y": d["bbox_y"], "w": d["bbox_w"], "h": d["bbox_h"]},
            "overlay_color": overlay_color,
        }

        # Add polygon data if available
        if d["points_json"]:
            detection["polygon"] = {"points_json": d["points_json"], "simplified": d["simplified"]}

        detections_data.append(detection)
        grouped_detections[d["label"]].append(
            {
                "id": d["id"],
                "confidence": d["confidence"],
                "overlay_color": overlay_color,
                "crop_url": f"/api/detections/{d['id']}/crop",
            }
        )

    # Use same-origin proxy URL so canvas-based polygon crops work in local environments.
    original_url = f"/api/gallery/{image_id}/asset"

    return templates.TemplateResponse(
        "pages/product_detail.html",
        {
            "request": request,
            "file_id": image_id,
            "original_url": original_url,
            "image_width": image["width"],
            "image_height": image["height"],
            "object_count": object_count,
            "classes": class_names,
            "grouped_detections": dict(grouped_detections),
            "detections_json": json.dumps(detections_data),  # JSON string for JavaScript
            "timestamp": image["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S") if image["uploaded_at"] else "",
        },
    )


@router.get("/api/gallery/{image_id}/asset")
async def gallery_image_asset(image_id: str, db: DatabaseDependency, storage: StorageDependency):
    if db is None:
        raise HTTPException(status_code=503, detail="Gallery is unavailable on the free profile")

    image = await db.get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    image_bytes = storage.download_bytes(image["storage_url"])
    if image_bytes is None:
        raise HTTPException(status_code=404, detail="Image asset not found")

    return Response(content=image_bytes, media_type=_get_media_type_from_key(image["storage_url"]))


@router.get("/api/detections/{detection_id}/crop")
async def detection_crop_asset(detection_id: str, db: DatabaseDependency, storage: StorageDependency):
    if db is None:
        raise HTTPException(status_code=503, detail="Gallery is unavailable on the free profile")

    detection = await db.get_detection(detection_id)
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")

    image = await db.get_image(detection["image_id"])
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    image_bytes = storage.download_bytes(image["storage_url"])
    if image_bytes is None:
        raise HTTPException(status_code=404, detail="Image asset not found")

    crop_bytes = _build_polygon_crop(image_bytes, detection)
    if crop_bytes is None:
        raise HTTPException(status_code=404, detail="Crop asset not available")

    return Response(content=crop_bytes, media_type="image/png")


@router.get("/api/gallery")
async def api_gallery(
    request: Request,
    db: DatabaseDependency,
    storage: StorageDependency,
    limit: int = 50,
):
    """
    API endpoint to get gallery data as JSON.
    """
    if db is None:
        return {"images": [], "count": 0, "available": False}

    # Fetch all images with detection counts
    images_data = await db.fetch_all(
        """SELECT i.id, i.storage_url, i.width, i.height, i.file_size, i.uploaded_at,
                  COUNT(d.id) as detection_count
           FROM images i
           LEFT JOIN detections d ON d.image_id = i.id
           GROUP BY i.id
           ORDER BY i.uploaded_at DESC
           LIMIT %s""",
        (limit,),
    )

    image_ids = [img["id"] for img in images_data]
    detections_by_image = await _fetch_detections_by_image(db, image_ids)

    result = []
    for img in images_data:
        detections = detections_by_image.get(img["id"], [])

        # Get public URLs
        original_url = storage.get_public_url(img["storage_url"], request_host=request.headers.get("host"))
        result.append(
            {
                "id": img["id"],
                "original_url": original_url,
                "width": img["width"],
                "height": img["height"],
                "file_size": img["file_size"],
                "uploaded_at": img["uploaded_at"].isoformat() if img["uploaded_at"] else None,
                "detection_count": img["detection_count"] or 0,
                "detections": [
                    {
                        "id": d["id"],
                        "label": d["label"],
                        "confidence": d["confidence"],
                        "bbox": {"x": d["bbox_x"], "y": d["bbox_y"], "w": d["bbox_w"], "h": d["bbox_h"]},
                    }
                    for d in detections
                ],
            }
        )

    return {"images": result, "count": len(result)}


@router.get("/api/gallery/{image_id}")
async def api_gallery_image(image_id: str, db: DatabaseDependency, storage: StorageDependency):
    """
    Get detailed info for a specific image including all detections with polygons.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Gallery is unavailable on the free profile")

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
        (image_id,),
    )

    # Get URLs
    original_url = storage.get_public_url(image["storage_url"])
    return {
        "id": image["id"],
        "original_url": original_url,
        "width": image["width"],
        "height": image["height"],
        "uploaded_at": image["uploaded_at"].isoformat() if image["uploaded_at"] else None,
        "detections": [
            {
                "id": d["id"],
                "label": d["label"],
                "confidence": d["confidence"],
                "bbox": {"x": d["bbox_x"], "y": d["bbox_y"], "w": d["bbox_w"], "h": d["bbox_h"]},
                "polygon": d["points_json"] if d["points_json"] else None,
            }
            for d in detections
        ],
    }
