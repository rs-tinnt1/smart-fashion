# app/services/web.py
import os
import json
from datetime import datetime
from ..config import OUTPUT_DIR


def build_gallery_data() -> list:
    """Prepare data for the gallery template."""
    output_files = list(OUTPUT_DIR.glob("*_output.jpg"))
    images = []

    for img_path in sorted(output_files, key=os.path.getmtime, reverse=True):
        file_id = img_path.stem.replace("_output", "")
        json_path = OUTPUT_DIR / f"{file_id}_data.json"
        if json_path.exists():
            with open(json_path) as f:
                data = json.load(f)
            images.append({
                "file_id": file_id,
                "image_url": f"/outputs/{img_path.name}",
                "object_count": len(data["objects"]),
                "classes": list({obj["class_name"] for obj in data["objects"]}),
                "timestamp": datetime.fromtimestamp(os.path.getmtime(img_path))
                             .strftime("%Y-%m-%d %H:%M:%S")
            })
    return images