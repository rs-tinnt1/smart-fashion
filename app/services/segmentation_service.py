import json
import uuid
from typing import Any

import cv2
import numpy as np
import threading
from app.config import MODEL_PRELOAD
from app.services.inference_service import load_best_segment_model
from app.services.runtime_status import set_runtime_component, add_runtime_warning

_model = None
_model_name = None
_model_lock = threading.Lock()

def get_loaded_model(storage_service, request_app=None) -> Any:
    global _model, _model_name
    if _model is not None:
        return _model
    
    with _model_lock:
        if _model is not None:
            return _model
        try:
            _model, _model_name = load_best_segment_model(storage_service)
            if request_app:
                set_runtime_component(request_app, "model", True, f"loaded on demand: {_model_name}")
            return _model
        except Exception as exc:
            if request_app:
                set_runtime_component(request_app, "model", False, str(exc))
                add_runtime_warning(request_app, f"On-demand model load failed: {exc}")
            raise RuntimeError(f"Model failed to initialize: {exc}") from exc

def preload_model(storage_service, request_app=None):
    global _model, _model_name
    try:
        _model, _model_name = load_best_segment_model(storage_service)
        if request_app:
            set_runtime_component(request_app, "model", True, f"loaded: {_model_name}")
        return _model, _model_name
    except Exception as exc:
        if request_app:
            set_runtime_component(request_app, "model", False, str(exc))
            add_runtime_warning(request_app, f"Model preload failed: {exc}")
        raise

def is_model_loaded() -> bool:
    return _model is not None

def get_loaded_model_name() -> str | None:
    return _model_name


def _contour_to_points(contour: Any) -> list[dict[str, int]]:
    points = np.asarray(contour).reshape(-1, 2)
    return [{"x": int(x), "y": int(y)} for x, y in points.tolist()]


def _process_one_image(image_bytes: bytes, model: Any) -> dict[str, Any]:
    """Process image to extract segmentation data WITHOUT drawing on the image.
    Returns polygon data for client-side rendering."""
    arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image")

    results = model(image, conf=0.25, iou=0.45, retina_masks=True)

    export_data = {"image_width": image.shape[1], "image_height": image.shape[0], "objects": []}

    result = results[0]
    has_boxes = result.boxes is not None and len(result.boxes) > 0

    if not has_boxes:
        return {"json_data": export_data}

    class_ids = result.boxes.cls.cpu().numpy()
    confidences = result.boxes.conf.cpu().numpy()
    boxes_xyxy = result.boxes.xyxy.cpu().numpy()
    class_names = result.names
    img_height, img_width = image.shape[:2]

    # ── Path A: Segmentation model (has masks) ──────────────────────────────
    if result.masks is not None:
        masks = result.masks.data.cpu().numpy()

        for i, mask in enumerate(masks):
            bbox = boxes_xyxy[i]
            bbox_x1, bbox_y1, bbox_x2, bbox_y2 = (int(value) for value in bbox[:4])
            x1, y1, x2, y2 = bbox_x1, bbox_y1, bbox_x2, bbox_y2

            # Expand bbox slightly (5% each side) to avoid cutting edges
            bbox_margin = 0.05
            bbox_w = x2 - x1
            bbox_h = y2 - y1
            x1 = max(0, int(x1 - bbox_w * bbox_margin))
            y1 = max(0, int(y1 - bbox_h * bbox_margin))
            x2 = min(img_width, int(x2 + bbox_w * bbox_margin))
            y2 = min(img_height, int(y2 + bbox_h * bbox_margin))

            mask_resized = cv2.resize(mask, (img_width, img_height), interpolation=cv2.INTER_LINEAR)

            bbox_mask = np.zeros_like(mask_resized)
            bbox_mask[y1:y2, x1:x2] = 1.0
            mask_resized = mask_resized * bbox_mask

            mask_threshold = 0.75
            mask_binary = (mask_resized > mask_threshold).astype(np.uint8) * 255

            kernel_size = max(5, int(min(img_width, img_height) * 0.01))
            if kernel_size % 2 == 0:
                kernel_size += 1

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_OPEN, kernel, iterations=2)
            mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_CLOSE, kernel, iterations=2)

            blur_size = max(3, kernel_size - 2)
            if blur_size % 2 == 0:
                blur_size += 1
            mask_binary = cv2.GaussianBlur(mask_binary, (blur_size, blur_size), 0)

            _, mask_binary = cv2.threshold(mask_binary, 127, 255, cv2.THRESH_BINARY)

            contours, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                contours = sorted(contours, key=cv2.contourArea, reverse=True)
                largest_area = cv2.contourArea(contours[0])
                contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= largest_area * 0.20]
                contours = [cv2.approxPolyDP(cnt, 0.001 * cv2.arcLength(cnt, True), True) for cnt in contours]

            contours_data = [_contour_to_points(contour) for contour in contours]

            export_data["objects"].append(
                {
                    "id": i,
                    "class_id": int(class_ids[i]),
                    "class_name": class_names[int(class_ids[i])],
                    "confidence": float(confidences[i]),
                    "bbox": {
                        "x": bbox_x1,
                        "y": bbox_y1,
                        "w": bbox_x2 - bbox_x1,
                        "h": bbox_y2 - bbox_y1,
                    },
                    "contours": contours_data,
                }
            )

    # ── Path B: Detection-only model (no masks) — use GrabCut to extract polygon ──
    else:
        for i in range(len(class_ids)):
            bbox = boxes_xyxy[i]
            bbox_x1, bbox_y1, bbox_x2, bbox_y2 = (int(value) for value in bbox[:4])
            x1, y1, x2, y2 = bbox_x1, bbox_y1, bbox_x2, bbox_y2

            # Ensure boundaries
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(img_width, x2), min(img_height, y2)

            w, h = x2 - x1, y2 - y1

            contours_data = []
            rect: tuple[int, int, int, int] = (x1, y1, w, h)

            # Attempt to extract precise foreground mask using GrabCut
            if w > 10 and h > 10:
                try:
                    gc_mask = np.zeros((img_height, img_width), np.uint8)
                    bgd_model = np.zeros((1, 65), np.float64)
                    fgd_model = np.zeros((1, 65), np.float64)

                    # Run GrabCut for 3 iterations
                    cv2.grabCut(image, gc_mask, rect, bgd_model, fgd_model, 3, cv2.GC_INIT_WITH_RECT)

                    # 0, 2 are background; 1, 3 are foreground
                    mask_binary = np.where((gc_mask == 1) | (gc_mask == 3), 255, 0).astype("uint8")

                    # Cleanup mask with morphology
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                    mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_OPEN, kernel, iterations=1)
                    mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_CLOSE, kernel, iterations=2)

                    contours, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    if contours:
                        contours = sorted(contours, key=cv2.contourArea, reverse=True)
                        largest_area = cv2.contourArea(contours[0])

                        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= largest_area * 0.15]

                        # Smooth polygons
                        smoothed = []
                        for cnt in valid_contours:
                            epsilon = 0.002 * cv2.arcLength(cnt, True)
                            approx = cv2.approxPolyDP(cnt, epsilon, True)
                            if len(approx) > 2:
                                smoothed.append(approx)

                        if smoothed:
                            contours_data = [_contour_to_points(contour) for contour in smoothed]
                except Exception as e:
                    print(f"GrabCut failed for bbox {rect}: {e}")

            # Fallback strictly to rectangle if GrabCut returned empty contours
            if not contours_data:
                rect_polygon = [
                    {"x": x1, "y": y1},
                    {"x": x2, "y": y1},
                    {"x": x2, "y": y2},
                    {"x": x1, "y": y2},
                ]
                contours_data = [rect_polygon]

            export_data["objects"].append(
                {
                    "id": i,
                    "class_id": int(class_ids[i]),
                    "class_name": class_names[int(class_ids[i])],
                    "confidence": float(confidences[i]),
                    "bbox": {
                        "x": bbox_x1,
                        "y": bbox_y1,
                        "w": bbox_x2 - bbox_x1,
                        "h": bbox_y2 - bbox_y1,
                    },
                    "contours": contours_data,
                }
            )

    return {"json_data": export_data}


def segment_one_file(
    image_bytes: bytes,
    filename: str,
    content_type: str,
    storage_service: Any | None,
    request_host: str | None = None,
    request_app: Any | None = None,
) -> dict[str, Any]:
    """Handle a single uploaded file – uploads ORIGINAL image & JSON to S3/R2 directly from memory.

    Args:
        image_bytes: Raw image bytes
        filename: Original filename
        content_type: MIME type of the upload
        storage_service: S3/R2 storage service instance
        request_host: Request host header for dynamic URLs
        request_app: FastAPI application instance for runtime warnings
    """
    if not content_type.startswith("image/"):
        raise ValueError(f"File {filename} is not an image")

    file_id = str(uuid.uuid4())
    model = get_loaded_model(storage_service, request_app=request_app)
    result = _process_one_image(image_bytes, model)

    file_ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    original_image_key = None
    original_image_url = None
    json_url = None

    json_bytes = json.dumps(result["json_data"]).encode("utf-8")

    if storage_service is not None:
        original_candidate_key = f"images/{file_id}.{file_ext}"
        json_key = f"outputs/{file_id}_data.json"

        if storage_service.upload_bytes(image_bytes, original_candidate_key, content_type=content_type):
            original_image_key = original_candidate_key
            original_image_url = storage_service.get_public_url(original_candidate_key, request_host=request_host)

        if storage_service.upload_bytes(json_bytes, json_key, content_type="application/json"):
            json_url = storage_service.get_public_url(json_key, request_host=request_host)

    return {
        "filename": filename,
        "file_id": file_id,
        "segmentation_data": result["json_data"],
        "original_image_url": original_image_url,
        "original_image_key": original_image_key,  # For database storage_url
        "json_url": json_url,
    }


def delete_output(file_id: str, storage_service: Any, image_storage_url: str | None = None) -> list[str]:
    """Delete output files and original image for a given file_id from S3/R2."""
    output_json_key = f"outputs/{file_id}_data.json"
    deleted = []

    # Delete original image using DB URL or fallback extensions
    if image_storage_url:
        storage_key = image_storage_url
        if storage_service.object_exists(storage_key):
            storage_service.delete_object(storage_key)
            deleted.append("original_image")
    else:
        for ext in ["jpg", "png", "jpeg", "webp"]:
            fallback_img_key = f"images/{file_id}.{ext}"
            if storage_service.object_exists(fallback_img_key):
                storage_service.delete_object(fallback_img_key)
                deleted.append(f"original_image_{ext}")
                break

    # Delete metadata JSON object
    if storage_service.object_exists(output_json_key):
        storage_service.delete_object(output_json_key)
        deleted.append("json")

    return deleted


def get_stats() -> dict[str, Any]:
    """Collect statistics about processed images. Note: Local stats disabled in Zero Disk I/O mode."""
    return {"total_images": 0, "total_objects": 0, "class_distribution": {}, "average_objects_per_image": 0}
