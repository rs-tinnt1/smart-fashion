# Smart Fashion - Clothing Segmentation API

FastAPI application for clothing segmentation using Ultralytics YOLO segmentation models.

## Quick Start

### Using Makefile (Recommended)

```bash
# Show all available commands
make help

# Install dependencies
make install

# Run development server
make dev

# Run tests
make test
```

### Local Development (Poetry)

```bash
# Install dependencies
make install
# or: poetry install

# Run development server
make dev
# or: poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000 --workers 1

# Run tests
make test
# or: poetry run pytest
```

### Docker Development

```bash
# Start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

Or using docker-compose directly:

```bash
docker compose -f compose.yml up -d
docker compose -f compose.yml logs -f app
```

### Podman Development

```bash
# Start all services
make podman-up

# View logs
make podman-logs

# Stop services
make podman-down
```

Or using podman-compose directly:

```bash
podman-compose -f compose.yml up -d
podman-compose -f compose.yml logs -f app
```

### Production Deployment

```bash
# Build and deploy
make prod-up

# Stop production
make prod-down
```

Or manually:

```bash
podman build -t smartfashion:latest -f Dockerfile .
podman-compose -f compose.prod.yml up -d
```

## Makefile Commands

| Command | Description |
| --- | --- |
| `make help` | Show all available commands |
| `make install` | Install dependencies with Poetry |
| `make dev` | Start development server |
| `make test` | Run all tests |
| `make test-cov` | Run tests with coverage |
| `make test-level1` | Run infrastructure tests |
| `make test-level2` | Run service tests |
| `make test-level3` | Run API tests |
| `make test-level4` | Run UI tests |
| `make format` | Format code with ruff |
| `make lint` | Lint code with ruff |
| `make fix` | Fix linting issues |
| `make docker-up` | Start all services (Docker) |
| `make docker-down` | Stop services (Docker) |
| `make docker-logs` | Follow app logs (Docker) |
| `make docker-build` | Rebuild app container |
| `make podman-up` | Start all services (Podman) |
| `make podman-down` | Stop services (Podman) |
| `make podman-logs` | Follow app logs (Podman) |
| `make podman-build` | Build image with Podman |
| `make prod-up` | Deploy production |
| `make prod-down` | Stop production |
| `make db-shell` | Open MariaDB shell |
| `make db-reset` | Reset database (removes all data) |
| `make minio-ls` | List files in MinIO bucket |
| `make minio-policy` | Set bucket policy to public |
| `make clean` | Remove cache and temp files |

## API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/` | GET | Web UI |
| `/api/segment` | POST | Upload images for segmentation |
| `/api/health` | GET | Health check |
| `/gallery` | GET | Image gallery |

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `UVICORN_WORKERS` | 1 | Number of workers |
| `UVICORN_PORT` | 8000 | Server port |
| `OMP_NUM_THREADS` | 4 | CPU threads for model inference |
| `MODEL_SEGMENT` | `yolo26n-seg.pt` | Primary segmentation model key in object storage |
| `MODEL_SEGMENT_FALLBACK` | `yolo11n-seg.pt` | Fallback model key if the primary model fails |

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
│   │   ├── inference_service.py        # Ultralytics YOLO wrapper
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
├── Makefile                            # Simplified commands
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
from app.services.storage_service import get_storage_service
from app.services.inference_service import YOLOSegmentation

from app.models.detection_schema import BBox, DetectionSummary, PolygonData
from app.models.image_schema import ImageResponse
from app.models.job_schema import JobStatus

# Or use package-level imports (via __init__.py)
from app.services import get_database, segment_one_file, YOLOSegmentation
from app.models import DetectionSummary, ImageResponse, JobStatus
from app.controllers import segment_router, gallery_router, upload_router
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test level
make test-level1
make test-level2
make test-level3
make test-level4
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Fix linting issues
make fix
```
