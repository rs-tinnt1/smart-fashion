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
    """Exact copy of your original process_image() – unchanged."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    results = model(image, conf=0.25, iou=0.45, retina_masks=True)
    output_image = image.copy()
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
            # ===== MASK PROCESSING V4 - Use bounding box to constrain mask =====
            
            # Get bounding box for this detection
            bbox = boxes_xyxy[i]  # [x1, y1, x2, y2]
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            
            # Expand bbox slightly (5% each side) to avoid cutting edges
            # Lower margin = tighter mask, better for multi-person images
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
            
            # Step 2: Apply bounding box constraint - zero out everything outside bbox
            # This is the KEY fix for background bleeding
            bbox_mask = np.zeros_like(mask_resized)
            bbox_mask[y1:y2, x1:x2] = 1.0
            mask_resized = mask_resized * bbox_mask
            
            # Step 3: VERY HIGH threshold (0.75) to eliminate uncertain areas
            MASK_THRESHOLD = 0.75
            mask_binary = (mask_resized > MASK_THRESHOLD).astype(np.uint8) * 255
            
            # Step 4: Morphological operations
            kernel_size = max(5, int(min(img_width, img_height) * 0.01))
            if kernel_size % 2 == 0:
                kernel_size += 1
            
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            
            # MORPH_OPEN: Loại bỏ nhiễu nhỏ
            mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_OPEN, kernel, iterations=2)
            
            # MORPH_CLOSE: Lấp lỗ hổng
            mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            # Step 4: Gaussian blur nhẹ
            blur_size = max(3, kernel_size - 2)
            if blur_size % 2 == 0:
                blur_size += 1
            mask_binary = cv2.GaussianBlur(mask_binary, (blur_size, blur_size), 0)
            
            # Step 5: Final threshold
            _, mask_binary = cv2.threshold(mask_binary, 127, 255, cv2.THRESH_BINARY)

            # Step 6: Find contours
            contours, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)
            
            # Step 7: KEEP ONLY THE LARGEST CONTOUR - Fix background noise issue
            # Mỗi detection chỉ nên có 1 contour chính (trang phục)
            # Các contour nhỏ hơn thường là noise hoặc background
            if contours:
                # Sắp xếp theo diện tích giảm dần
                contours = sorted(contours, key=cv2.contourArea, reverse=True)
                
                # Chỉ giữ contour lớn nhất
                # Nếu muốn giữ nhiều hơn, có thể giữ các contour > 20% của contour lớn nhất
                largest = contours[0]
                largest_area = cv2.contourArea(largest)
                
                # Giữ contour lớn nhất và các contour >= 20% diện tích của nó
                MIN_RATIO = 0.20
                filtered = [largest]
                for cnt in contours[1:]:
                    if cv2.contourArea(cnt) >= largest_area * MIN_RATIO:
                        filtered.append(cnt)
                
                contours = filtered
                
                # Step 8: Polygon approximation nhẹ để làm mịn (KHÔNG dùng convex hull)
                # Convex hull làm mất chi tiết như tay áo, cổ áo
                smoothed_contours = []
                for contour in contours:
                    # Douglas-Peucker với epsilon nhỏ (0.1% chu vi) để giữ chi tiết
                    epsilon = 0.001 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    smoothed_contours.append(approx)
                
                contours = smoothed_contours

            class_id = int(class_ids[i])
            class_name = class_names[class_id]
            confidence = confidences[i]
            color = COLORS[i % len(COLORS)]
            color_rgb = (color[2], color[1], color[0])

            # Visualization với contours đã được cải thiện
            overlay = output_image.copy()
            cv2.drawContours(overlay, contours, -1, color, -1)
            alpha = 0.4
            output_image = cv2.addWeighted(overlay, alpha, output_image, 1 - alpha, 0)
            
            # Vẽ đường viền dày hơn và mịn hơn với anti-aliasing
            cv2.drawContours(output_image, contours, -1, color, 2, cv2.LINE_AA)

            # Export contours data
            contours_data = [
                [{"x": int(p[0][0]), "y": int(p[0][1])} for p in contour]
                for contour in contours
            ]

            # label (same as original)
            label_position = None
            if contours:
                top_point = tuple(contours[0][0][0])
                label = f"{class_name} {confidence:.2f}"
                label_position = {"x": int(top_point[0]), "y": int(top_point[1]) - 10}
                (lw, lh), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                )
                cv2.rectangle(
                    output_image,
                    (top_point[0], top_point[1] - lh - baseline - 5),
                    (top_point[0] + lw, top_point[1] - 5),
                    color, -1
                )
                cv2.putText(
                    output_image, label, (top_point[0], top_point[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
                )

            object_data = {
                "id": i,
                "class_id": class_id,
                "class_name": class_name,
                "confidence": float(confidence),
                "color": {"r": color_rgb[0], "g": color_rgb[1], "b": color_rgb[2]},
                "contours": contours_data,
                "label": {"text": f"{class_name} {confidence:.2f}", "position": label_position},
                "fill_alpha": alpha
            }
            export_data["objects"].append(object_data)

    output_image_path = OUTPUT_DIR / f"{output_prefix}_output.jpg"
    json_path = OUTPUT_DIR / f"{output_prefix}_data.json"
    cv2.imwrite(str(output_image_path), output_image)
    with open(json_path, "w") as f:
        json.dump(export_data, f, indent=2)

    return {
        "output_image": str(output_image_path),
        "json_data": export_data,
        "json_file": str(json_path)
    }


def segment_one_file(file_obj, model: Any, minio_service: Any, base_url: str = "") -> Dict[str, Any]:
    """Handle a single uploaded file – called from the /segment endpoint."""
    if not file_obj.content_type.startswith("image/"):
        raise ValueError(f"File {file_obj.filename} is not an image")

    file_id = str(uuid.uuid4())
    input_path = _save_upload(file_obj, file_id)

    try:
        result = _process_one_image(str(input_path), file_id, model)
        
        # Upload output image to MinIO
        output_image_path = Path(result["output_image"])
        output_image_key = f"outputs/{file_id}_output.jpg"
        minio_service.upload_file(output_image_path, output_image_key, content_type="image/jpeg")
        
        # Upload JSON data to MinIO
        json_file_path = Path(result["json_file"])
        json_key = f"outputs/{file_id}_data.json"
        minio_service.upload_file(json_file_path, json_key, content_type="application/json")
        
        # Get presigned URLs
        output_image_url = minio_service.get_presigned_url(output_image_key)
        json_url = minio_service.get_presigned_url(json_key)
        
        # Clean up local output files
        output_image_path.unlink(missing_ok=True)
        json_file_path.unlink(missing_ok=True)
        
        return {
            "filename": file_obj.filename,
            "file_id": file_id,
            "segmentation_data": result["json_data"],
            "output_image_url": output_image_url,
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