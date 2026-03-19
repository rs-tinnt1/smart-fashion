# Smart Fashion - Clothing Segmentation & Detection API

FastAPI backend application for clothing item detection and polygon segmentation using Ultralytics YOLO models coupled with OpenCV GrabCut algorithms for zero-disk-I/O processing.

---

## 🌟 Key Features & Architecture

* **Zero Disk I/O Pipeline**: Images are processed entirely in-memory using `BytesIO` and Numpy buffers. Files are never written to local disk, maximizing throughput and reducing wear.
* **Hybrid Segmentation (YOLO + GrabCut)**: Uses YOLO `detect-only` models (e.g., `yolov8n-clothing-detection`) to tightly bound clothing items, then dynamically applies OpenCV's **GrabCut** algorithm to extract highly accurate, form-fitting polygons for the frontend canvas.
* **Cloudflare R2 Storage**: Integrated with S3-compatible object storage using dynamically generated **Presigned URLs** to securely serve files without exposing the bucket to public access (resolving 403 Forbidden errors).
* **Cascading MySQL Database**: Utilizes `aiomysql` to connect to cloud databases (like Aiven). Fully implements `ON DELETE CASCADE` to instantly wipe orphaned data across `images`, `detections`, and `polygons` when an item is deleted.
* **Windows-Ready AsyncIO**: Built-in support for `asyncio.WindowsSelectorEventLoopPolicy` to prevent SSL tunnel crashes when connecting to secure cloud databases from local Windows development environments.

## 🚀 Quick Start

### Using Makefile (Recommended)

```bash
# Show all available commands
make help

# Install dependencies (Poetry)
make install

# Run development server
make dev

# Run tests
make test
```

### Local Development (Poetry)

```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000 --workers 1
```

### Production Deployment

Use the included `compose.prod.yml` or `render.yaml` for Docker-based web service deployments. Configure `MODEL_PRELOAD=false` on heavily constrained environments so the app can pass health checks before downloading the YOLO weights.

## 🛠️ Configuration (.env)

| Variable | Default | Description |
| --- | --- | --- |
| `UVICORN_WORKERS` | 1 | Number of ASGI workers |
| `OMP_NUM_THREADS` | 4 | CPU threads allocated strictly for model inference |
| `MODEL_SEGMENT` | `yolov8n-clothing-detection.pt` | Primary detection/segmentation model key in object storage |
| `MODEL_SEGMENT_FALLBACK` | `yolo11n-seg.pt` | Fallback model key if the primary model fails to load |
| `DB_URL` | | Connection string for MariaDB/MySQL (e.g., Aiven) |
| `S3_ENDPOINT` | | Cloudflare R2 endpoint |
| `S3_BUCKET` | | Bucket Name |
| `S3_ACCESS_KEY_ID` / `SECRET` | | S3 Credentials |

## 📂 Project Structure

```text
├── app/
│   ├── controllers/                    # API routes (FastAPI routers)
│   │   ├── segment_controller.py       # Segmentation API & Cascade Deletion
│   │   ├── gallery_controller.py       # Gallery & product detail views
│   │   └── upload_controller.py        # Upload & job status endpoints
│   ├── models/                         # Pydantic schemas (request/response)
│   ├── services/                       # Business logic & infrastructure
│   │   ├── segmentation_service.py     # Core OpenCV Grabcut + Polygon logic
│   │   ├── inference_service.py        # Ultralytics YOLO inference wrapper
│   │   ├── database_service.py         # aiomysql operations
│   │   ├── storage_service.py          # Boto3 S3/R2 operations & Presigned URLs
│   │   └── web_service.py              # Web utilities
│   └── config.py                       # Configuration settings
├── templates/                          # Jinja2 HTML templates
├── static/                             # Static assets (CSS, JS, images)
├── db/                                 # SQL schemas with ON DELETE CASCADE
├── docs/                               # Legacy documentation & plans
├── main.py                             # FastAPI application entry point
├── Dockerfile                          # Production container image
└── pyproject.toml                      # Poetry dependencies
```

### Architecture Principles

**Flat Architecture**: Files use descriptive names with suffixes instead of deep nesting.
- ✅ `services/database_service.py` - Clear, flat structure
- ❌ `services/database/service.py` - Unnecessary nesting

**Dependency Flow**: `Controllers` ➔ `Services` ➔ `Models` (Strict unidirectional flow to prevent circular imports).

## 🧪 Development & Testing

```bash
# Format code
make format

# Lint code 
make lint

# Fix linting issues
make fix

# Reset local database (removes all data)
make db-reset
```
