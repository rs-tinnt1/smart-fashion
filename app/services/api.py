# app/services/api.py
from pathlib import Path
import uuid
import shutil
import json
from typing import List, Dict, Any

from ultralytics import YOLO
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


def _process_one_image(image_path: str, output_prefix: str, model: YOLO) -> Dict[str, Any]:
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
        class_names = results[0].names
        img_height, img_width = image.shape[:2]

        for i, mask in enumerate(masks):
            mask_resized = cv2.resize(mask, (img_width, img_height),
                                      interpolation=cv2.INTER_CUBIC)
            mask_binary = (mask_resized > 0.35).astype(np.uint8) * 255
            kernel = np.ones((5, 5), np.uint8)
            mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_CLOSE, kernel)
            mask_binary = cv2.GaussianBlur(mask_binary, (5, 5), 0)
            mask_binary = (mask_binary > 127).astype(np.uint8) * 255

            contours, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)

            class_id = int(class_ids[i])
            class_name = class_names[class_id]
            confidence = confidences[i]
            color = COLORS[i % len(COLORS)]
            color_rgb = (color[2], color[1], color[0])

            overlay = output_image.copy()
            cv2.drawContours(overlay, contours, -1, color, -1)
            alpha = 0.4
            output_image = cv2.addWeighted(overlay, alpha, output_image, 1 - alpha, 0)
            cv2.drawContours(output_image, contours, -1, color, 3)

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


def segment_one_file(file_obj, model: YOLO) -> Dict[str, Any]:
    """Handle a single uploaded file – called from the /segment endpoint."""
    if not file_obj.content_type.startswith("image/"):
        raise ValueError(f"File {file_obj.filename} is not an image")

    file_id = str(uuid.uuid4())
    input_path = _save_upload(file_obj, file_id)

    try:
        result = _process_one_image(str(input_path), file_id, model)
        return {
            "filename": file_obj.filename,
            "file_id": file_id,
            "segmentation_data": result["json_data"],
            "output_image_url": f"/outputs/{file_id}_output.jpg",
            "json_url": f"/outputs/{file_id}_data.json"
        }
    finally:
        _delete_input(input_path)


def delete_output(file_id: str) -> List[str]:
    """Delete output files for a given file_id."""
    output_img = OUTPUT_DIR / f"{file_id}_output.jpg"
    output_json = OUTPUT_DIR / f"{file_id}_data.json"
    deleted = []
    if output_img.exists():
        output_img.unlink()
        deleted.append("image")
    if output_json.exists():
        output_json.unlink()
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