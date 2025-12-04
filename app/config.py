import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Model paths
ONNX_MODEL_PATH = os.getenv("ONNX_MODEL_PATH", "models/deepfashion2_yolov8s-seg.onnx")

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
STATIC_DIR = Path("static")

# DB settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/smartfashion")
MONGO_DB = os.getenv("MONGO_DB", "smartfashion")

# MinIO config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "123456")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "smartfashion")
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

COLORS = [
    (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (128, 0, 128), (0, 128, 255),
    (255, 128, 0), (128, 255, 0), (0, 128, 128), (128, 128, 0),
]