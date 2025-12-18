# app/services/api.py
from pathlib import Path
import uuid
import shutil
import json
from typing import List, Dict, Any

import cv2
import numpy as np

from ..config import UPLOAD_DIR, OUTPUT_DIR, COLORS  # will be created later


def _save_upload(file_obj, file_id: str) -> Path:
    """Save the uploaded file and return its path."""
    file_extension = Path(file_obj.filename).suffix
    input_path = UPLOAD_DIR / f"{file_id}{file_extension}"
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file_obj.file, buffer)
    return input_path


def _delete_input(input_path: Path):
    """Delete the temporary input file."""
    if input_path.exists():
        input_path.unlink()


def _process_one_image(image_path: str, output_prefix: str, model: Any) -> Dict[str, Any]:
    """Process image to extract segmentation data WITHOUT drawing on the image.
    Returns polygon data for client-side rendering."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    results = model(image, conf=0.25, iou=0.45, retina_masks=True)
    
    export_data = {
        "image_width": image.shape[1],
        "image_height": image.shape[0],
        "objects": []
    }

    if results[0].masks is not None:
        masks = results[0].masks.data.cpu().numpy()
        class_ids = results[0].boxes.cls.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()
        boxes_xyxy = results[0].boxes.xyxy.cpu().numpy()  # Get bounding boxes [x1, y1, x2, y2]
        class_names = results[0].names
        img_height, img_width = image.shape[:2]

        for i, mask in enumerate(masks):
            # ===== MASK PROCESSING - Extract polygon data only =====
            
            # Get bounding box for this detection
            bbox = boxes_xyxy[i]  # [x1, y1, x2, y2]
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            
            # Expand bbox slightly (5% each side) to avoid cutting edges
            bbox_margin = 0.05
            bbox_w = x2 - x1
            bbox_h = y2 - y1
            x1 = max(0, int(x1 - bbox_w * bbox_margin))
            y1 = max(0, int(y1 - bbox_h * bbox_margin))
            x2 = min(img_width, int(x2 + bbox_w * bbox_margin))
            y2 = min(img_height, int(y2 + bbox_h * bbox_margin))
            
            # Step 1: Resize mask
            mask_resized = cv2.resize(mask, (img_width, img_height),
                                      interpolation=cv2.INTER_LINEAR)
            
            # Step 2: Apply bounding box constraint
            bbox_mask = np.zeros_like(mask_resized)
            bbox_mask[y1:y2, x1:x2] = 1.0
            mask_resized = mask_resized * bbox_mask
            
            # Step 3: High threshold to eliminate uncertain areas
            MASK_THRESHOLD = 0.75
            mask_binary = (mask_resized > MASK_THRESHOLD).astype(np.uint8) * 255
            
            # Step 4: Morphological operations
            kernel_size = max(5, int(min(img_width, img_height) * 0.01))
            if kernel_size % 2 == 0:
                kernel_size += 1
            
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_OPEN, kernel, iterations=2)
            mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            # Step 5: Gaussian blur
            blur_size = max(3, kernel_size - 2)
            if blur_size % 2 == 0:
                blur_size += 1
            mask_binary = cv2.GaussianBlur(mask_binary, (blur_size, blur_size), 0)
            
            # Step 6: Final threshold
            _, mask_binary = cv2.threshold(mask_binary, 127, 255, cv2.THRESH_BINARY)

            # Step 7: Find contours
            contours, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)
            
            # Step 8: Keep only significant contours
            if contours:
                contours = sorted(contours, key=cv2.contourArea, reverse=True)
                largest = contours[0]
                largest_area = cv2.contourArea(largest)
                
                # Keep largest and contours >= 20% of it
                MIN_RATIO = 0.20
                filtered = [largest]
                for cnt in contours[1:]:
                    if cv2.contourArea(cnt) >= largest_area * MIN_RATIO:
                        filtered.append(cnt)
                
                contours = filtered
                
                # Step 9: Polygon approximation for smoothing
                smoothed_contours = []
                for contour in contours:
                    epsilon = 0.001 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    smoothed_contours.append(approx)
                
                contours = smoothed_contours

            class_id = int(class_ids[i])
            class_name = class_names[class_id]
            confidence = confidences[i]

            # Export contours data (no visualization)
            contours_data = [
                [{"x": int(p[0][0]), "y": int(p[0][1])} for p in contour]
                for contour in contours
            ]

            object_data = {
                "id": i,
                "class_id": class_id,
                "class_name": class_name,
                "confidence": float(confidence),
                "bbox": {
                    "x": int(bbox[0]),
                    "y": int(bbox[1]),
                    "w": int(bbox[2] - bbox[0]),
                    "h": int(bbox[3] - bbox[1])
                },
                "contours": contours_data
            }
            export_data["objects"].append(object_data)

    # Save only JSON data (no output image)
    json_path = OUTPUT_DIR / f"{output_prefix}_data.json"
    with open(json_path, "w") as f:
        json.dump(export_data, f, indent=2)

    return {
        "original_image": image_path,  # Return original image path
        "json_data": export_data,
        "json_file": str(json_path)
    }


def segment_one_file(file_obj, model: Any, minio_service: Any, base_url: str = "", request_host: str = None) -> Dict[str, Any]:
    """Handle a single uploaded file – uploads ORIGINAL image to MinIO.
    
    Args:
        file_obj: Uploaded file object
        model: YOLO model for inference
        minio_service: MinIO service instance
        base_url: Base URL of the application
        request_host: Request host header for dynamic MinIO URLs
    """
    if not file_obj.content_type.startswith("image/"):
        raise ValueError(f"File {file_obj.filename} is not an image")

    file_id = str(uuid.uuid4())
    input_path = _save_upload(file_obj, file_id)

    try:
        result = _process_one_image(str(input_path), file_id, model)
        
        # Upload ORIGINAL image to MinIO (not output image)
        original_image_path = Path(result["original_image"])
        original_image_key = f"images/{file_id}{original_image_path.suffix}"
        minio_service.upload_file(original_image_path, original_image_key, content_type="image/jpeg")
        
        # Upload JSON data to MinIO
        json_file_path = Path(result["json_file"])
        json_key = f"outputs/{file_id}_data.json"
        minio_service.upload_file(json_file_path, json_key, content_type="application/json")
        
        # Get public URLs
        original_image_url = minio_service.get_public_url(original_image_key, request_host=request_host)
        json_url = minio_service.get_public_url(json_key, request_host=request_host)
        
        # Clean up local files
        json_file_path.unlink(missing_ok=True)
        
        return {
            "filename": file_obj.filename,
            "file_id": file_id,
            "segmentation_data": result["json_data"],
            "original_image_url": original_image_url,
            "original_image_key": original_image_key,  # For database storage_url
            "json_url": json_url
        }
    finally:
        _delete_input(input_path)


def delete_output(file_id: str, minio_service: Any) -> List[str]:
    """Delete output files for a given file_id from MinIO."""
    output_img_key = f"outputs/{file_id}_output.jpg"
    output_json_key = f"outputs/{file_id}_data.json"
    deleted = []
    if minio_service.object_exists(output_img_key):
        minio_service.delete_object(output_img_key)
        deleted.append("image")
    if minio_service.object_exists(output_json_key):
        minio_service.delete_object(output_json_key)
        deleted.append("json")
    return deleted


def get_stats() -> Dict[str, Any]:
    """Collect statistics about processed images."""
    json_files = list(OUTPUT_DIR.glob("*_data.json"))
    total_images = len(json_files)
    total_objects = 0
    class_counts: Dict[str, int] = {}

    for json_path in json_files:
        with open(json_path) as f:
            data = json.load(f)
        total_objects += len(data["objects"])
        for obj in data["objects"]:
            class_counts[obj["class_name"]] = class_counts.get(obj["class_name"], 0) + 1

    avg = round(total_objects / total_images, 2) if total_images else 0
    return {
        "total_images": total_images,
        "total_objects": total_objects,
        "class_distribution": class_counts,
        "average_objects_per_image": avg
    }