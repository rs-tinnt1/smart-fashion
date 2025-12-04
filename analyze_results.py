import json
from pathlib import Path
import statistics

output_dir = Path(r"e:\Workspace\Backend\python\smart-fashion\outputs")
json_files = list(output_dir.glob("*_data.json"))

total_images = len(json_files)
total_objects = 0
all_confidences = []
class_counts = {}
low_conf_objects = []

print(f"Analyzing {total_images} JSON files...")

for json_file in json_files:
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        objects = data.get("objects", [])
        total_objects += len(objects)
        
        for obj in objects:
            cls_name = obj.get("class_name", "unknown")
            conf = obj.get("confidence", 0.0)
            
            all_confidences.append(conf)
            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
            
            if conf < 0.5:
                low_conf_objects.append({
                    "file": json_file.name,
                    "class": cls_name,
                    "confidence": conf
                })
                
    except Exception as e:
        print(f"Error reading {json_file}: {e}")

print("-" * 30)
print(f"Total Images: {total_images}")
print(f"Total Objects Detected: {total_objects}")
if total_images > 0:
    print(f"Avg Objects per Image: {total_objects / total_images:.2f}")

if all_confidences:
    print(f"Average Confidence: {statistics.mean(all_confidences):.4f}")
    print(f"Min Confidence: {min(all_confidences):.4f}")
    print(f"Max Confidence: {max(all_confidences):.4f}")

print("-" * 30)
print("Class Distribution:")
for cls, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {cls}: {count}")

print("-" * 30)
if low_conf_objects:
    print(f"Low Confidence Detections (< 0.5): {len(low_conf_objects)}")
    for obj in low_conf_objects[:5]:
        print(f"  {obj['file']}: {obj['class']} ({obj['confidence']:.4f})")
else:
    print("No low confidence detections (< 0.5) found.")
