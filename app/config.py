import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# Model paths
MODEL_SEGMENT = os.getenv("MODEL_SEGMENT", "yolo11m-seg.pt")
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

# S3/R2 config (Cloudflare R2 is S3-compatible)
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://account.r2.cloudflarestorage.com")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "smartfashion")
S3_REGION = os.getenv("S3_REGION", "auto")  # R2 uses 'auto' for region

COLORS = [
    (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (128, 0, 128), (0, 128, 255),
    (255, 128, 0), (128, 255, 0), (0, 128, 128), (128, 128, 0),
]
