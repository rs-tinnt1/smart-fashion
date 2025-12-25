# Smart Fashion - Clothing Segmentation API

FastAPI application for clothing segmentation using YOLOv8 with ONNX Runtime.

## Quick Start

### Local Development (Poetry)

```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000 --workers 1

# Run tests
poetry run pytest
```

### Docker Development

- Docker command

```bash
docker-compose up -d

docker-compose logs -f app
```

- Podman command

```bash
podman-compose up -d

podman-compose logs -f app
```

### Production Deployment

- Docker command

```bash
podman build -t smartfashion:latest .
podman-compose -f compose.prod.yml up -d
```

- Podman command

```bash
podman build -t smartfashion:latest .
podman-compose -f compose.prod.yml up -d
```

## API Endpoints

| Endpoint       | Method | Description                    |
| -------------- | ------ | ------------------------------ |
| `/`            | GET    | Web UI                         |
| `/api/segment` | POST   | Upload images for segmentation |
| `/api/health`  | GET    | Health check                   |
| `/gallery`     | GET    | Image gallery                  |

## Configuration

| Variable          | Default                       | Description          |
| ----------------- | ----------------------------- | -------------------- |
| `UVICORN_WORKERS` | 1                             | Number of workers    |
| `UVICORN_PORT`    | 8000                          | Server port          |
| `OMP_NUM_THREADS` | 4                             | CPU threads for ONNX |
| `MINIO_MODEL_KEY` | deepfashion2_yolov8s-seg.onnx | Model file in MinIO  |

## Project Structure

```
├── app/
│   ├── controllers/                    # API routes (FastAPI routers)
│   │   ├── segment_controller.py       # Segmentation API endpoints
│   │   ├── gallery_controller.py       # Gallery & product detail views
│   │   └── upload_controller.py        # Upload & job status endpoints
│   ├── models/                         # Pydantic schemas (request/response)
│   │   ├── detection_schema.py         # BBox, Polygon, Detection models
│   │   ├── image_schema.py             # Image metadata models
│   │   ├── upload_schema.py            # Upload response models
│   │   ├── job_schema.py               # Job status models
│   │   └── health_schema.py            # Health check models
│   ├── services/                       # Business logic & infrastructure
│   │   ├── segmentation_service.py     # Core segmentation logic
│   │   ├── inference_service.py        # ONNX Runtime wrapper
│   │   ├── database_service.py         # MariaDB operations
│   │   ├── storage_service.py          # MinIO/S3 operations
│   │   └── web_service.py              # Web utilities
│   └── config.py                       # Configuration settings
├── templates/                          # Jinja2 HTML templates
├── static/                             # Static assets (CSS, JS, images)
├── tests/                              # 4-level integration tests
├── db/                                 # Database schema (SQL)
├── docs/                               # Documentation
├── worker.py                           # Background job processor
├── main.py                             # FastAPI application entry point
├── Dockerfile                          # Production container image
├── compose.yml                         # Development environment
├── compose.prod.yml                    # Production environment
├── pyproject.toml                      # Poetry dependencies
└── poetry.lock                         # Locked dependency versions
```

### Architecture Principles

**Flat Architecture**: Files use descriptive names with suffixes instead of deep nesting
- ✅ `services/database_service.py` - Clear, flat structure
- ❌ `services/database/service.py` - Unnecessary nesting

**Naming Conventions**:
- Controllers: `*_controller.py` (e.g., `segment_controller.py`)
- Services: `*_service.py` (e.g., `database_service.py`)
- Models: `*_schema.py` (e.g., `detection_schema.py`)

**Dependency Flow**: Controllers → Services → Models (no circular dependencies)

### Import Examples

```python
# Import from specific modules
from app.services.segmentation_service import segment_one_file
from app.services.database_service import get_database, DatabaseService
from app.services.storage_service import get_minio_service
from app.services.inference_service import ONNXYOLOSegmentation

from app.models.detection_schema import BBox, DetectionSummary, PolygonData
from app.models.image_schema import ImageResponse
from app.models.job_schema import JobStatus

# Or use package-level imports (via __init__.py)
from app.services import get_database, segment_one_file, ONNXYOLOSegmentation
from app.models import DetectionSummary, ImageResponse, JobStatus
from app.controllers import segment_router, gallery_router, upload_router
```

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test level
poetry run pytest tests/test_level1_infrastructure.py -v
```

### Code Quality

```bash
# Format code
poetry run ruff format .

# Lint code
poetry run ruff check .
```
