# AGENT TASK: Refactor FastAPI Image Processing Pipeline — Zero Disk I/O

## Context & Objective

You are refactoring a **Python FastAPI** backend that handles clothing item detection using a YOLO segmentation model (`yolo26n-seg`). The current implementation writes images to temporary folders on disk at every stage. Your goal is to eliminate all unnecessary disk I/O by implementing a fully in-memory pipeline using `BytesIO`, numpy buffers, and async streaming — with the YOLO model loaded once at application startup.

**Do not ask for confirmation between steps. Execute all phases sequentially and output a structured report at the end.**

---

## Phase 1 — Codebase Discovery

Before making any changes, explore and map the existing structure:

1. List all files and directories in the project root (including `app/`, `src/`, `routers/`, `services/`, `core/`, `models/`, `schemas/`).
2. Find all route handlers that accept image uploads (search for `UploadFile`, `File(...)`, `Form(...)`, `multipart`).
3. Find all references to temporary file operations:
   ```bash
   grep -rn "tmp\|tempfile\|NamedTemporaryFile\|mkdtemp\|os\.path\|shutil\|open(" --include="*.py"
   ```
4. Find all references to disk writes/reads inside the pipeline:
   ```bash
   grep -rn "\.write\|\.read\|\.save\|cv2\.imwrite\|cv2\.imread\|Image\.save\|Image\.open" --include="*.py"
   ```
5. Find where the YOLO model is loaded and invoked (search for `YOLO(`, `model =`, `model.predict`, `model(`, `ultralytics`).
6. Find where S3 upload happens (search for `boto3`, `s3_client`, `upload_file`, `put_object`, `upload_fileobj`).
7. Find the DB save logic for the image URL (search for `session`, `db`, `insert`, `create`, `commit`).
8. Read the content of every file identified in steps 2–7.
9. Identify the application entry point (`main.py`, `app.py`, or equivalent) and read it.
10. Read `requirements.txt` or `pyproject.toml` for existing dependencies.

Output a full summary of all findings before proceeding to Phase 2.

---

## Phase 2 — Dependency Verification

Check whether the following packages are already installed. Install only what is missing:

```bash
pip show boto3 pillow opencv-python-headless ultralytics fastapi python-multipart | grep -E "^(Name|---)"
```

Install missing packages if absent:

```bash
pip install python-multipart
```

> **Note**: Prefer `boto3` with `run_in_executor` for async S3 operations — avoids adding a new dependency. Do not remove `boto3` if it is already used elsewhere.

Update `requirements.txt` or `pyproject.toml` to reflect any newly added packages.

---

## Phase 3 — Create the YOLO Service Module

Locate the services directory (`services/`, `app/services/`, or equivalent). Create a new file `yolo_service.py` at that location. **Do not modify the existing YOLO-related code — create a new file.**

```python
# services/yolo_service.py
"""
YOLO inference service — in-memory, zero disk I/O.
Model is loaded once at startup via FastAPI lifespan.
"""
import asyncio
import os
from functools import partial
from io import BytesIO

import cv2
import numpy as np
from ultralytics import YOLO

_model: YOLO | None = None


def load_model() -> None:
    """Call once during application startup."""
    global _model
    model_path = os.getenv("YOLO_MODEL_PATH", "yolo26n-seg.pt")
    _model = YOLO(model_path)


def _run_inference(image_bytes: bytes) -> bytes:
    """
    Synchronous YOLO inference — runs in a thread pool executor.
    Accepts raw image bytes, returns annotated JPEG bytes.
    Never touches the filesystem.
    """
    if _model is None:
        raise RuntimeError("YOLO model is not loaded. Call load_model() at startup.")

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Cannot decode image — unsupported format or corrupted file.")

    results = _model(img)
    annotated = results[0].plot()

    quality = int(os.getenv("JPEG_QUALITY", "90"))
    _, encoded = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return encoded.tobytes()


async def detect_clothing(image_bytes: bytes) -> bytes:
    """
    Async wrapper — offloads blocking YOLO inference to a thread pool
    so the FastAPI event loop is never blocked.
    Returns annotated image as bytes.
    """
    loop = asyncio.get_running_loop()
    result: bytes = await loop.run_in_executor(None, partial(_run_inference, image_bytes))
    return result
```

---

## Phase 4 — Create the S3 Upload Service

Locate the existing S3 utility or service file. **Replace only the upload function** with the stream-based version below. Keep all other existing code in that file intact.

If no S3 file exists, create `services/s3_service.py`.

```python
# services/s3_service.py  (or replace upload function in existing file)
"""
S3 upload service — streams BytesIO directly to S3, zero disk I/O.
"""
import asyncio
import os
import uuid
from functools import partial
from io import BytesIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError

_s3_client = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION", "ap-southeast-1"),
)


def _upload_bytes_sync(image_bytes: bytes, key: str) -> str:
    """
    Synchronous S3 upload via upload_fileobj — streams BytesIO to S3.
    Runs in a thread pool to avoid blocking the event loop.
    Never writes to disk.
    """
    bucket = os.getenv("S3_BUCKET")
    if not bucket:
        raise RuntimeError("S3_BUCKET environment variable is not set.")

    buffer = BytesIO(image_bytes)

    try:
        _s3_client.upload_fileobj(
            buffer,
            bucket,
            key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"S3 upload failed: {e}") from e

    region = os.getenv("AWS_REGION", "ap-southeast-1")
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


async def upload_image_to_s3(image_bytes: bytes, original_filename: str) -> str:
    """
    Async wrapper — offloads blocking boto3 call to a thread pool.
    Returns the public S3 URL.
    """
    ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "jpg"
    key = f"detections/{uuid.uuid4().hex}.{ext}"

    loop = asyncio.get_running_loop()
    url: str = await loop.run_in_executor(
        None, partial(_upload_bytes_sync, image_bytes, key)
    )
    return url
```

---

## Phase 5 — Register YOLO Model at Application Startup

Locate the FastAPI application entry point (`main.py` or `app.py`). Replace or extend the existing startup logic to use FastAPI's **lifespan** context manager so the YOLO model is loaded exactly once and reused across all requests.

**If the file already uses `@app.on_event("startup")` — migrate it to `lifespan`:**

```python
# main.py — replace or extend existing startup
from contextlib import asynccontextmanager
from fastapi import FastAPI
from services.yolo_service import load_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — runs once before accepting requests
    load_model()
    yield
    # Shutdown — add cleanup here if needed


app = FastAPI(lifespan=lifespan)
```

> If a `lifespan` function already exists, add `load_model()` inside the existing startup block — do not create a second `lifespan`.

---

## Phase 6 — Refactor the Route Handler

Locate the route file that handles clothing detection uploads. **Rewrite only the handler body.** Preserve the existing route path (`@router.post(...)` or `@app.post(...)`), all `Depends(...)` parameters, authentication, and other decorators.

**Remove all of the following from the handler:**
- Any `tempfile.NamedTemporaryFile` / `tempfile.mkdtemp` usage
- Any `open(path, "wb")` / `open(path, "rb")` operating on a temp path
- Any `os.remove` / `os.unlink` / `shutil.rmtree` call
- Any `cv2.imwrite` / `cv2.imread` referencing a file path
- Any `subprocess.run` / `os.system` call that invokes YOLO via CLI
- Any `Image.save(path)` / `Image.open(path)` using a file path

**Replace the handler body with:**

```python
import asyncio
from fastapi import APIRouter, File, HTTPException, UploadFile
from services.yolo_service import detect_clothing
from services.s3_service import upload_image_to_s3

router = APIRouter()


@router.post("/detect")          # keep existing path and all decorators unchanged
async def detect_handler(
    file: UploadFile = File(...),
    # keep all existing Depends(...) and other parameters here
):
    # Validate content type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    # 1. Read upload into memory — no disk write
    image_bytes: bytes = await file.read()

    # 2. Run YOLO inference (blocking → thread pool) — no disk write
    try:
        result_bytes = await detect_clothing(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 3. Upload annotated result to S3 — streams BytesIO, no disk write
    try:
        s3_url = await upload_image_to_s3(result_bytes, file.filename or "result.jpg")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 4. Persist to DB — keep existing DB save logic, pass the new URL
    record = await save_detection_record(
        url=s3_url,
        original_name=file.filename,
        mime_type=file.content_type,
        # keep any other fields your model requires
    )

    return {"url": s3_url, "id": record.id}
```

> **Parallel upload variant**: If the project also uploads the *original* image to S3 alongside the annotated result, replace step 2–3 with `asyncio.gather` to run inference and original-image upload concurrently:
>
> ```python
> result_bytes, original_url = await asyncio.gather(
>     detect_clothing(image_bytes),
>     upload_image_to_s3(image_bytes, file.filename or "original.jpg"),
> )
> annotated_url = await upload_image_to_s3(result_bytes, f"annotated-{file.filename}")
> ```

---

## Phase 7 — Update Environment Variables

Check if a `.env`, `.env.example`, or equivalent configuration file exists. Add the following variables if they are not already defined. **Do not overwrite existing values.**

```dotenv
# YOLO
YOLO_MODEL_PATH=yolo26n-seg.pt
JPEG_QUALITY=90

# AWS
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=your-key-id
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET=your-bucket-name
```

---

## Phase 8 — Cleanup

1. Search all Python files for remaining temp-file operations inside the detection pipeline:
   ```bash
   grep -rn "NamedTemporaryFile\|mkdtemp\|tmpdir\|/tmp/" --include="*.py"
   ```
   For each match:
   - Inside the upload/detection pipeline → **remove it**.
   - Elsewhere (unrelated code) → **leave untouched**, log in the final report.

2. Search for orphaned imports in modified files (`import tempfile`, `import shutil`, `import subprocess`) that are no longer used after the refactor. Remove them only from files that were modified in this task.

3. Do **not** delete any test files, Alembic migration files, or configuration files.

---

## Phase 9 — Verification

After all changes, run these checks without starting the server:

1. **Syntax check** — verify no syntax errors in all modified and created files:
   ```bash
   python -m py_compile services/yolo_service.py
   python -m py_compile services/s3_service.py
   python -m py_compile main.py
   # also compile the modified route file
   ```

2. **Grep check** — confirm no temp-file disk operations remain in the pipeline:
   ```bash
   grep -rn "NamedTemporaryFile\|imwrite\|open(.*['\"]wb\|open(.*['\"]rb" --include="*.py" \
     routers/ services/ app/ src/ 2>/dev/null
   ```
   Any result inside a detection or upload handler is a failure — report it.

3. **Model path check** — confirm the YOLO model file exists at the default path:
   ```bash
   ls -lh yolo26n-seg.pt 2>/dev/null || echo "WARNING: model file not found at default path"
   ```

---

## Completion Report

After all phases, output a structured report in this exact format:

```
## Refactor Summary

### Files modified
- <path>: <what changed>

### Files created
- <path>: <purpose>

### Dependencies added
- <package>: <reason>

### Disk I/O removed
- <file>:<line> — <description of removed operation>

### Disk I/O remaining (if any)
- <file>:<line> — <reason it was intentionally kept>

### Verification results
- Syntax check: PASS / FAIL (<details if fail>)
- Grep check: PASS / FAIL (<remaining references if fail>)
- Model file: FOUND / NOT FOUND at <path>

### Manual steps required after this refactor
- <action the developer must take, e.g. set env vars, copy model file, restart service>
```

---

## Constraints

- Do not change database schema, ORM models, or query logic unless strictly necessary to pass the new URL.
- Do not change authentication, CORS, rate-limiting, or middleware configuration.
- Do not upgrade or downgrade any dependency version not listed in this task.
- Do not convert synchronous DB calls to async or vice versa — preserve the existing DB access pattern.
- If a file cannot be safely modified due to ambiguity, **report it and skip** rather than guess.
- All new code must be compatible with the Python version already in use by the project.