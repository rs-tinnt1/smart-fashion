# Smart Fashion - Clothing Segmentation & Detection API

FastAPI backend application for clothing item detection and polygon segmentation using Ultralytics YOLO with Cloudflare R2 storage and MySQL.

---

## 🌟 Key Features & Architecture

* **R2-backed image pipeline**: Images and JSON metadata are stored in Cloudflare R2 via presigned URLs.
* **YOLO clothing segmentation**: Loads a single model, `yolov8n-clothing-detection.pt`, from object storage and generates polygon data for the frontend canvas.
* **MySQL job and metadata storage**: Uses `aiomysql` for image, detection, polygon, embedding, and worker job records.
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

Use `render.yaml` for the web service or `render.worker.yaml` for web + worker deployments. Configure `MODEL_PRELOAD=false` on constrained environments so the app can pass health checks before downloading the YOLO weights.

If you want to avoid long Docker builds on Render, use the image-backed blueprints in `render.image.yaml` and `render.image.worker.yaml`. The repository now includes `.github/workflows/build-image.yml`, which publishes a `linux/amd64` image to GHCR and can optionally trigger Render deploy hooks via the `RENDER_WEBHOOK_URL` and `RENDER_WORKER_WEBHOOK_URL` secrets.

### Render Free Profile

The home page is tuned for a single free Render web service:

- uploads stay on the home page and run one image at a time
- the queue is local to the browser with a hard limit of 100 images
- `POST /api/segment` no longer requires the database to succeed
- gallery and history features degrade gracefully when `DB_URL` is not configured

This profile keeps the app usable on Render Free, but it is still best-effort: cold starts and the first lazy model load can still be slow.

### Local Demo Workflow

The `develop` branch is intended for the full local demo flow: multi-image upload, database-backed queue, background worker processing, and polygon masks.

- start the web app and worker together with `docker compose -f compose.yml up --build`
- the compose stack starts local `mysql`, `minio`, `app`, and `worker` services automatically
- MySQL loads `db/schema.sql` on first boot, and MinIO creates the `smartfashion` bucket for local object storage
- local containers talk to MinIO via `http://minio:9000`, while the browser loads images through `S3_PUBLIC_ENDPOINT=http://localhost:9000`
- if you want to keep using a hosted database or external object storage, set `DB_URL` and S3 variables before starting compose to override the local defaults
- the home page uploads images immediately, then polls background jobs until the worker finishes them

## 🛠️ Configuration (.env)

| Variable | Default | Description |
| --- | --- | --- |
| `UVICORN_WORKERS` | 1 | Number of ASGI workers |
| `OMP_NUM_THREADS` | 4 | CPU threads allocated strictly for model inference |
| `MODEL_SEGMENT` | `yolov8n-clothing-detection.pt` | Primary detection/segmentation model key in object storage |
| `DB_URL` | | Connection string for MySQL-compatible databases (e.g., local Docker or Aiven) |
| `S3_ENDPOINT` | | S3-compatible endpoint (e.g., local MinIO or Cloudflare R2) |
| `S3_PUBLIC_ENDPOINT` | | Browser-facing object storage endpoint for local/containerized setups |
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

# Start app + worker with external services from `.env`
make docker-up
```
