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
│   ├── controllers/          # API routes
│   ├── models/               # Data models
│   └── services/
│       ├── api.py            # Core segmentation logic
│       ├── onnx_inference.py # ONNX Runtime wrapper
│       ├── database.py       # Database service
│       └── minio_service.py  # MinIO service
├── templates/                # Jinja2 templates
├── static/                   # Static files (JS)
├── tests/                    # Integration tests
├── db/                       # Database schema
├── Dockerfile                # Production-optimized
├── compose.yml               # Development
├── compose.prod.yml          # Production
├── pyproject.toml            # Poetry configuration
└── poetry.lock               # Locked dependencies
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
