import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

load_dotenv()

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")


def _get_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def _get_bool_env(*names: str, default: bool = False) -> bool:
    value = _get_env(*names)
    if not value:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int_env(*names: str, default: int) -> int:
    value = _get_env(*names)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


# Model paths
MODEL_SEGMENT = _get_env("MODEL_SEGMENT", default="yolov8n-clothing-detection.pt")
MODEL_PRELOAD = _get_bool_env("MODEL_PRELOAD", default=True)
LOCAL_MODEL_CACHE = Path(os.getenv("LOCAL_MODEL_CACHE", "/tmp/models"))

UVICORN_HOST = _get_env("UVICORN_HOST", default="0.0.0.0")
UVICORN_PORT = _get_int_env("PORT", "UVICORN_PORT", default=8000)
UVICORN_WORKERS = _get_int_env("UVICORN_WORKERS", default=1)

STATIC_DIR = Path("static")

# DB settings (MariaDB/MySQL) - parse from connection string
DB_URL = _get_env(
    "DB_URL",
    default=(
        f"mysql://{_get_env('DB_USER', default='smartfashion')}:{_get_env('DB_PASSWORD', default='smartfashion')}"
        f"@{_get_env('DB_HOST', default='localhost')}:{_get_env('DB_PORT', default='3306')}"
        f"/{_get_env('DB_NAME', default='smartfashion')}"
    ),
)
_parsed_db = urlparse(DB_URL)
_db_query = {key.lower(): values[-1] for key, values in parse_qs(_parsed_db.query).items()}
DB_HOST = _parsed_db.hostname or "localhost"
DB_PORT = _parsed_db.port or 3306
DB_USER = _parsed_db.username or "smartfashion"
DB_PASSWORD = _parsed_db.password or "smartfashion"
DB_NAME = _parsed_db.path.lstrip("/") or "smartfashion"
DB_CONNECT_TIMEOUT = _get_int_env("DB_CONNECT_TIMEOUT", default=10)
DB_SSL_MODE = _get_env("DB_SSL_MODE", default=_db_query.get("ssl-mode", _db_query.get("sslmode", ""))).lower()
DB_SSL = _get_bool_env("DB_SSL", default=DB_SSL_MODE in {"required", "verify_ca", "verify_identity"})
DB_SSL_CA = _get_env("DB_SSL_CA", default=_db_query.get("ssl-ca", _db_query.get("ssl_ca", "")))
DB_SSL_CERT = _get_env("DB_SSL_CERT", default=_db_query.get("ssl-cert", _db_query.get("ssl_cert", "")))
DB_SSL_KEY = _get_env("DB_SSL_KEY", default=_db_query.get("ssl-key", _db_query.get("ssl_key", "")))

# S3/R2 config (Cloudflare R2 is S3-compatible)
S3_ENDPOINT = _get_env("S3_ENDPOINT", default="https://account.r2.cloudflarestorage.com")
S3_ACCESS_KEY_ID = _get_env("S3_ACCESS_KEY_ID", default="")
S3_SECRET_ACCESS_KEY = _get_env("S3_SECRET_ACCESS_KEY", default="")
S3_BUCKET = _get_env("S3_BUCKET", default="smartfashion")
S3_REGION = _get_env("S3_REGION", default="auto")
