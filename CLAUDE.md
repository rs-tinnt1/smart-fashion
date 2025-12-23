# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Smart Fashion** is a FastAPI-based web application for detecting and segmenting clothing items in images using YOLOv8 with ONNX Runtime. The system provides real-time clothing segmentation with polygon masks, bounding boxes, and confidence scores.

**Tech Stack:**
- **Backend:** FastAPI 0.115+ (Python 3.12)
- **ML Model:** YOLOv8 Segmentation (ONNX Runtime)
- **Database:** MariaDB 11.x
- **Storage:** MinIO (S3-compatible object storage)
- **Frontend:** Vanilla JavaScript with HTML5 Canvas
- **Deployment:** Docker/Podman
- **Package Manager:** Poetry

---

## Development Commands

### Setup & Installation

```bash
# Install dependencies
poetry install

# Copy environment file and configure
cp .env.example .env
```

### Running the Application

```bash
# Local development (without Docker)
# Start services only (MariaDB + MinIO)
docker-compose up -d mariadb minio

# Run dev server
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000 --workers 1

# Docker development (all services)
docker-compose up -d

# View logs
docker-compose logs -f app

# Rebuild after code changes
docker-compose up -d --build app
```

### Testing

```bash
# Run all tests
poetry run pytest -v

# Run specific test level
poetry run pytest tests/test_level1_infrastructure.py -v
poetry run pytest tests/test_level2_services.py -v
poetry run pytest tests/test_level3_api.py -v
poetry run pytest tests/test_level4_ui.py -v

# Run single test function
poetry run pytest tests/test_level3_api.py::test_segment_endpoint -v

# Run with coverage
poetry run pytest --cov=app

# Generate HTML coverage report
poetry run pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code
poetry run ruff format .

# Lint code
poetry run ruff check .

# Fix linting issues
poetry run ruff check . --fix
```

### Database Operations

```bash
# Access MariaDB CLI
docker-compose exec mariadb mysql -u smartfashion -psmartfashion smartfashion

# Common queries
# SELECT * FROM images ORDER BY uploaded_at DESC LIMIT 10;
# SELECT * FROM detections WHERE image_id = 1;
# SELECT * FROM polygons WHERE detection_id = 1;

# Reset database (removes all data)
docker-compose down -v && docker-compose up -d
```

### MinIO Operations

```bash
# List files in bucket
docker-compose exec minio mc ls minio/smartfashion/

# Set bucket policy to public read (if images not displaying)
docker-compose exec minio mc policy set download minio/smartfashion

# Upload model manually
docker-compose exec minio mc cp /path/to/model.onnx minio/smartfashion/
```

### Production Deployment

```bash
# Build optimized image
podman build -t smartfashion:latest .

# Deploy with production compose
podman-compose -f compose.prod.yml up -d

# Check health
curl http://localhost:8000/api/health
```

---

## Architecture

### System Components

```
┌─────────────────┐
│   Web Client    │
│  (HTML/JS/CSS)  │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────────────────────────┐
│          FastAPI App                │
│  ┌──────────────────────────────┐  │
│  │   Controllers (Routers)      │  │
│  │  - api_controller.py         │  │
│  │  - gallery_controller.py     │  │
│  │  - upload_controller.py      │  │
│  └──────────┬───────────────────┘  │
│             ▼                       │
│  ┌──────────────────────────────┐  │
│  │   Services (Business Logic)  │  │
│  │  - api.py (segmentation)     │  │
│  │  - onnx_inference.py (ML)    │  │
│  │  - database.py               │  │
│  │  - minio_service.py          │  │
│  └──────────┬───────────────────┘  │
└─────────────┼───────────────────────┘
              │
      ┌───────┴────────┐
      ▼                ▼
┌──────────┐    ┌──────────────┐
│ MariaDB  │    │    MinIO     │
│ Database │    │ (S3 Storage) │
└──────────┘    └──────────────┘
```

### Application Lifecycle

The application uses FastAPI's `lifespan` context manager (main.py:18-72) for dependency management:

1. **Startup:**
   - Initialize MinIO service
   - Download ONNX model from MinIO to local cache (`/tmp/models/`)
   - Load ONNX model into memory using ONNXYOLOSegmentation
   - Inject model and MinIO service into controllers
   - Initialize database connection pool

2. **Runtime:**
   - Serve HTTP requests via FastAPI routers
   - Process images using injected model
   - Store results in MariaDB + MinIO

3. **Shutdown:**
   - Close database connection pool gracefully

### Database Schema

**Key Tables:**
- `images` - Uploaded images metadata (id, filename, upload_time, minio_key)
- `detections` - Detected clothing items (image_id, bbox coordinates, confidence, label)
- `polygons` - Segmentation masks stored as JSON arrays of polygon coordinates
- `embeddings` - Feature vectors for similarity search (future enhancement)
- `product_tags` - Custom tags for detected items
- `jobs` - Async processing queue (status: pending/processing/done/error)

**Critical Relationships:**
- `images` 1→N `detections` (CASCADE DELETE)
- `detections` 1→N `polygons` (CASCADE DELETE)

See [db/schema.sql](db/schema.sql) for complete schema.

### Request Flow

#### Synchronous Segmentation (`POST /api/segment`):
1. User uploads image(s) → api_controller.py:segment_clothes()
2. Controller validates files → calls api.py:segment_clothes_batch()
3. Service loads image → onnx_inference.py:predict()
4. ONNX model returns boxes + masks → extract polygons from masks
5. Store image in MinIO + metadata/detections/polygons in MariaDB
6. Return JSON response with polygons, bboxes, confidence scores

#### Asynchronous Upload (`POST /api/upload`):
1. User uploads image(s) → upload_controller.py:upload_image()
2. Store image in MinIO + create job record in database (status='pending')
3. Return job_id to client immediately
4. Background worker.py polls for pending jobs
5. Worker processes image → updates job status → stores detections
6. Client polls `GET /api/jobs/{job_id}` for results

---

## Code Navigation Guide

### Adding/Modifying Features

**Segmentation Logic:**
- [`app/services/api.py`](app/services/api.py)
  - `_process_one_image()`: Polygon extraction from ONNX masks
  - `segment_one_file()`: Main processing function
  - Uses cv2.findContours() to convert binary masks to polygons

**ONNX Inference:**
- [`app/services/onnx_inference.py`](app/services/onnx_inference.py)
  - `ONNXYOLOSegmentation`: ONNX model wrapper
  - `predict()`: Runs inference + NMS + postprocessing
  - `preprocess()`: Image preprocessing (resize, normalize)

**API Endpoints:**
- [`app/controllers/api_controller.py`](app/controllers/api_controller.py) - Core segmentation API
- [`app/controllers/gallery_controller.py`](app/controllers/gallery_controller.py) - Gallery + image listing
- [`app/controllers/upload_controller.py`](app/controllers/upload_controller.py) - Async upload workflow

**Database Operations:**
- [`app/services/database.py`](app/services/database.py)
  - `DatabaseService` class with async methods
  - Connection pooling with `aiomysql`
  - Methods: `store_image()`, `store_detection()`, `store_polygon()`, `get_image_with_detections()`

**Object Storage:**
- [`app/services/minio_service.py`](app/services/minio_service.py)
  - `upload_file()`, `download_file()`, `get_public_url()`
  - Handles internal vs external endpoint URLs for browser access

**Frontend:**
- [`static/product-detail.js`](static/product-detail.js) - Canvas mask rendering
- [`static/gallery.js`](static/gallery.js) - Gallery pagination
- [`static/home.js`](static/home.js) - Upload page logic

**Background Worker:**
- [`worker.py`](worker.py) - Polls database for pending jobs, processes images asynchronously

---

## Environment Variables

**Critical Configuration** (see [.env.example](.env.example)):

```bash
# App
APP_VERSION=2.0.0
UVICORN_WORKERS=1          # Increase for production (e.g., 4)
UVICORN_PORT=8000
OMP_NUM_THREADS=4          # Match CPU cores for better ONNX performance

# Model
MINIO_MODEL_KEY=deepfashion2_yolov8s-seg.onnx
LOCAL_MODEL_CACHE=/tmp/models

# Database
DB_HOST=mariadb            # Use 'localhost' for local dev without Docker
DB_PORT=3306
DB_USER=smartfashion
DB_PASSWORD=smartfashion
DB_NAME=smartfashion

# MinIO
MINIO_ENDPOINT=http://minio:9000                    # Internal endpoint
MINIO_EXTERNAL_ENDPOINT=http://localhost:9000        # Browser-accessible URL
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=admin123456
MINIO_BUCKET=smartfashion
MINIO_SECURE=false         # Set 'true' for HTTPS
```

**Important:**
- `MINIO_ENDPOINT` is used by the app container to connect to MinIO
- `MINIO_EXTERNAL_ENDPOINT` is used for generating image URLs accessible from the browser
- For network access from other machines, set `MINIO_EXTERNAL_ENDPOINT` to your server's IP (e.g., `http://192.168.1.100:9000`)

---

## Testing Strategy

**4-Level Test Pyramid:**

1. **Level 1 - Infrastructure** (`test_level1_infrastructure.py`)
   - MariaDB connection and schema validation
   - MinIO connectivity and bucket operations

2. **Level 2 - Services** (`test_level2_services.py`)
   - DatabaseService CRUD operations
   - MinIO file upload/download
   - ONNX model loading and inference

3. **Level 3 - API** (`test_level3_api.py`)
   - `/api/segment` endpoint with valid/invalid files
   - `/api/upload` async workflow
   - Error handling (file size limits, invalid formats)

4. **Level 4 - UI** (`test_level4_ui.py`)
   - Template rendering (index.html, gallery.html, product-detail.html)
   - Gallery pagination
   - Product detail page

---

## Common Tasks

### Add a New Clothing Category
1. Update ONNX model with new class (retrain YOLOv8)
2. Update `COLORS` array in [`app/config.py`](app/config.py) if needed (for visualization)
3. No database changes needed (labels are stored as strings)

### Change Image Size Limits
Edit [`app/controllers/api_controller.py`](app/controllers/api_controller.py):
```python
MAX_FILE_SIZE_KB = 500  # Change this value
```

### Add Custom Image Preprocessing
Edit [`app/services/onnx_inference.py`](app/services/onnx_inference.py):
```python
def preprocess(self, img: np.ndarray) -> np.ndarray:
    # Add custom preprocessing here (e.g., color normalization, augmentation)
    ...
```

### Enable HTTPS for MinIO
Edit [`.env`](.env):
```bash
MINIO_SECURE=true
MINIO_ENDPOINT=https://your-minio-domain.com
MINIO_EXTERNAL_ENDPOINT=https://your-minio-domain.com
```

### Scale Workers for Production
Edit [`compose.prod.yml`](compose.prod.yml):
```yaml
environment:
  UVICORN_WORKERS: 4  # Increase workers (typically # of CPU cores)
```

### Modify Database Schema
1. Edit [`db/schema.sql`](db/schema.sql)
2. Recreate database: `docker-compose down -v && docker-compose up -d`
3. **Warning:** This deletes all data. For production, use migrations (e.g., Alembic)

---

## Troubleshooting

### Images not displaying (403 Forbidden)
**Cause:** MinIO bucket policy not public
**Fix:**
```bash
docker-compose exec minio mc policy set download minio/smartfashion
```

### Database connection errors
**Cause:** MariaDB not ready when app starts
**Fix:** Already implemented via healthcheck in `compose.yml` (line 38-40)

### ONNX model not loading
**Cause:** Model file missing in MinIO bucket
**Fix:**
```bash
# Upload model manually
docker-compose exec minio mc cp /path/to/model.onnx minio/smartfashion/
```

### Slow inference on CPU
**Cause:** OMP threads too low
**Fix:** Increase `OMP_NUM_THREADS` in `.env`:
```bash
OMP_NUM_THREADS=8  # Match CPU cores
```

### Model cache issues
**Cause:** Cached model corrupted or outdated
**Fix:**
```bash
# Remove cached model (will re-download on next startup)
rm -rf /tmp/models/*
# Or inside Docker:
docker-compose exec app rm -rf /tmp/models/*
```

---

## 🎨 Scandinavian UI Redesign

The project includes a **complete Scandinavian design system** for transforming the UI into an authentic Nordic aesthetic.

### Design Documentation

- [`docs/scandinavian_design_guide.md`](docs/scandinavian_design_guide.md) - Design principles, color palette, typography
- [`docs/scandinavian_redesign_plan.md`](docs/scandinavian_redesign_plan.md) - Step-by-step implementation guide
- [`docs/SCANDINAVIAN_QUICK_START.md`](docs/SCANDINAVIAN_QUICK_START.md) - Quick 3-step implementation
- [`static/scandinavian.css`](static/scandinavian.css) - Ready-to-use CSS design system

### Quick Implementation

```bash
# 1. Link CSS in templates (<head> section)
<link rel="stylesheet" href="/static/scandinavian.css?v={{ APP_VERSION }}">

# 2. Replace Tailwind classes with Scandinavian classes
<nav class="scandi-nav">
  <div class="scandi-nav__container">
    <div class="scandi-nav__logo">Smart Fashion</div>
    <a href="/" class="scandi-nav__link scandi-nav__link--active">Upload</a>
  </div>
</nav>

# 3. Test
poetry run uvicorn main:app --reload
```

### Design Tokens

```css
/* Primary Colors */
--scandi-dusty-blue: #6B8E9E;    /* Primary actions */
--scandi-sage-green: #9CAF88;    /* Secondary actions */
--scandi-warm-beige: #E8DCC4;    /* Tags, accents */
--scandi-off-white: #F5F5F5;     /* Background */

/* Component Classes */
.btn-primary                      /* Primary button */
.btn-secondary                    /* Secondary button */
.card                            /* Card container */
.tag                             /* Tag/badge */
.stat-card                       /* Statistic card */
```

---

## Additional Resources

- **Database Design:** [`docs/database_design.md`](docs/database_design.md)
- **Integration Tests:** [`docs/intergration_tests.md`](docs/intergration_tests.md)
- **MinIO URL Fix:** [`docs/minio_public_url_fix.md`](docs/minio_public_url_fix.md)

---

## API Endpoints Reference

| Endpoint | Method | Description | Request | Response |
|----------|--------|-------------|---------|----------|
| `/` | GET | Upload page UI | - | HTML |
| `/gallery` | GET | Image gallery UI | - | HTML |
| `/product/{image_id}` | GET | Product detail page | - | HTML |
| `/api/health` | GET | Health check | - | `{"status": "ok", "model_loaded": true}` |
| `/api/segment` | POST | Synchronous segmentation | `multipart/form-data` files | JSON with polygons/bboxes |
| `/api/upload` | POST | Async upload (background) | `multipart/form-data` files | `{"job_id": "..."}` |
| `/api/jobs/{job_id}` | GET | Poll job status | - | `{"status": "done", "result": {...}}` |
| `/api/images` | GET | List images | `?page=1&limit=12` | Paginated image list |
| `/api/images/{image_id}` | GET | Image details | - | Image + detections + polygons |
