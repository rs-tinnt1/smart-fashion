# Smart Fashion - Clothing Segmentation API

FastAPI application for clothing segmentation using YOLOv8 with ONNX Runtime.

## Quick Start

### 1. Build & Run

```bash
# Build image (~400MB)
podman build -t smartfashion:onnx .

# Run
podman-compose up -d
```

### 2. API Endpoints

- `GET /` - Web UI
- `POST /api/segment` - Upload images for segmentation
- `GET /api/health` - Health check

## Configuration

| Variable          | Default        | Description       |
| ----------------- | -------------- | ----------------- |
| `UVICORN_WORKERS` | 1              | Number of workers |
| `ONNX_MODEL_PATH` | models/...onnx | ONNX model path   |
| `OMP_NUM_THREADS` | 4              | CPU threads       |

## Project Structure

```
├── app/
│   ├── services/
│   │   ├── api.py            # Core segmentation logic
│   │   └── onnx_inference.py # ONNX Runtime wrapper
│   └── controllers/          # API routes
├── Dockerfile                # ONNX-optimized
├── compose.yml
└── requirements.txt
```
