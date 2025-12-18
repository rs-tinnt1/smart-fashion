import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# Model paths
ONNX_MODEL_PATH = os.getenv("ONNX_MODEL_PATH", "models/deepfashion2_yolov8s-seg.onnx")
MINIO_MODEL_KEY = os.getenv("MINIO_MODEL_KEY", "deepfashion2_yolov8s-seg.onnx")
LOCAL_MODEL_CACHE = Path(os.getenv("LOCAL_MODEL_CACHE", "/tmp/models"))

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
STATIC_DIR = Path("static")

# DB settings (MariaDB)
DB_HOST = os.getenv("DB_HOST", "mariadb")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "smartfashion")
DB_PASSWORD = os.getenv("DB_PASSWORD", "smartfashion")
DB_NAME = os.getenv("DB_NAME", "smartfashion")

# MinIO config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "admin123456")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "smartfashion")
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
# External endpoint for presigned URLs (browser-accessible)
MINIO_EXTERNAL_ENDPOINT = os.getenv("MINIO_EXTERNAL_ENDPOINT", "http://localhost:9000")

COLORS = [
    (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (128, 0, 128), (0, 128, 255),
    (255, 128, 0), (128, 255, 0), (0, 128, 128), (128, 128, 0),
]