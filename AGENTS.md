# Agent Guidelines for Smart Fashion

## Development Commands

### Package Management
```bash
poetry install                    # Install dependencies
poetry add <package>              # Add a new dependency
```

### Running the Application
```bash
# Local development (services only)
docker-compose up -d mariadb
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Docker development (all services)
docker-compose up -d
docker-compose logs -f app
```

### Testing
```bash
# Run all tests
poetry run pytest -v

# Run specific test level (4-level pyramid)
poetry run pytest tests/test_level1_infrastructure.py -v   # Infrastructure
poetry run pytest tests/test_level2_services.py -v         # Services
poetry run pytest tests/test_level3_api.py -v              # API
poetry run pytest tests/test_level4_ui.py -v               # UI

# Run single test class or function
poetry run pytest tests/test_level2_services.py::TestDatabaseService -v
poetry run pytest tests/test_level2_services.py::TestDatabaseService::test_create_and_get_image -v

# Run with coverage
poetry run pytest --cov=app --cov-report=html
```

### Code Quality
```bash
poetry run ruff format .          # Format code
poetry run ruff check .           # Lint code
poetry run ruff check . --fix     # Fix linting issues automatically
```

### Database Operations
```bash
docker-compose exec mariadb mysql -u smartfashion -psmartfashion smartfashion
docker-compose down -v && docker-compose up -d   # Reset database
```

## Code Style Guidelines

### Imports
Order: standard library -> third-party -> local (blank line separators)
```python
import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from app.config import S3_BUCKET
from app.services.database_service import get_database
```

### Type Hints
Use type hints for all functions. Use modern union syntax for Python 3.12:
```python
async def create_image(image_id: str, storage_url: str, width: int = 0) -> str:
def upload_file(self, local_path: str | Path, object_name: str) -> bool:
```

### Naming Conventions
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE` (in config.py only)
- Private methods: `_prefix_method_name`
- Test classes: `TestClassName`, test functions: `test_descriptive_name`

### Error Handling
Controllers raise `HTTPException`, services use try/except with print:
```python
# Controller
if not files:
    raise HTTPException(status_code=400, detail="No files provided")

# Service
try:
    self.client.upload_file(bucket, object_name, str(local_path))
except S3Error as e:
    print(f"Error uploading file: {e}")
    return False
```

### Service Layer Pattern
Use singleton pattern for services:
```python
class StorageService:
    _instance: Optional["StorageService"] = None

    @classmethod
    def get_instance(cls) -> "StorageService":
        if cls._instance is None:
            cls._instance = StorageService()
        return cls._instance
```

### Async/Await
All database operations use async/await with `aiomysql`:
```python
async def create_image(self, image_id: str, storage_url: str) -> str:
    query = "INSERT INTO images (id, storage_url) VALUES (%s, %s)"
    await self.execute(query, (image_id, storage_url))
    return image_id
```

### Dependency Injection
Use FastAPI `Depends` for controllers:
```python
@router.post("/api/segment")
async def segment_clothing(
    files: List[UploadFile] = File(...),
    model=Depends(get_model),
    storage=Depends(get_storage),
    db: DatabaseService = Depends(get_db)
):
```

### File Organization
- `app/controllers/` - FastAPI routers (API endpoints)
- `app/services/` - Business logic (database, storage, inference)
- `app/models/` - Pydantic schemas
- `app/config.py` - Configuration constants from environment
- `tests/` - 4-level test pyramid

### Configuration
All config via environment variables (see `.env.example`):
```python
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://account.r2.cloudflarestorage.com")
S3_BUCKET = os.getenv("S3_BUCKET", "smartfashion")
MODEL_SEGMENT = os.getenv("MODEL_SEGMENT", "yolo11m-seg.pt")
```

### S3/R2 Storage Key Structure
- Original images: `images/{file_id}.jpg`
- Output data: `outputs/{file_id}_data.json`
- Model: `yolo11m-seg.pt` (PyTorch format)

### Database Queries
Use parameterized queries to prevent SQL injection:
```python
query = "SELECT * FROM images WHERE id = %s"
result = await self.fetch_one(query, (image_id,))
```

### JSON Handling
Store JSON as string, parse on retrieval:
```python
await db.create_polygon(detection_id, points_json=json.dumps(contours))
points = json.loads(polygon['points_json'])
```

### File Path Handling
Use `pathlib.Path`:
```python
LOCAL_MODEL_CACHE = Path(os.getenv("LOCAL_MODEL_CACHE", "/tmp/models"))
LOCAL_MODEL_CACHE.mkdir(parents=True, exist_ok=True)
```

### Logging
Use print statements (no logging library):
```python
print(f"Loading model from {model_path}")
print(f"Database pool initialized: {DB_HOST}:{DB_PORT}/{DB_NAME}")
```

### Testing Conventions
- Use pytest markers: `@pytest.mark.level1`, `@pytest.mark.asyncio`
- Use `@pytest.mark.skipif` for conditional skipping
- Set `DB_HOST=localhost` for local testing without Docker

### Linting Rules (pyproject.toml)
- Target: Python 3.12, Line length: 120
- Ruff selects: E, F, W, I, N, UP, B, C4
- Ignored: E501 (line length handled by formatter)

### Important
- Never commit `.env` files or credentials
- Use `.env.example` as template
