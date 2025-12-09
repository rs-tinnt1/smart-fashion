from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.config import UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR, ONNX_MODEL_PATH, MINIO_MODEL_KEY, LOCAL_MODEL_CACHE, MINIO_BUCKET
from app.controllers.api_controller import router as api_router
from app.controllers.gallery_controller import router as gallery_router

app = FastAPI(
    title="Clothing Segmentation Web App",
    description="Web application for detecting and segmenting clothing items in images",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

templates = Jinja2Templates(directory="templates")

# MODEL loading - ONNX Runtime
model = None
minio_service = None

@app.on_event("startup")
async def load_model():
    global model, minio_service
    try:
        # Initialize MinIO service
        from app.services.minio_service import get_minio_service
        minio_service = get_minio_service()
        minio_service.ensure_bucket_exists()
        
        # Inject minio_service into api_controller
        import app.controllers.api_controller
        app.controllers.api_controller.minio_service = minio_service
        
        # Download model from MinIO
        LOCAL_MODEL_CACHE.mkdir(parents=True, exist_ok=True)
        local_model_path = LOCAL_MODEL_CACHE / MINIO_MODEL_KEY
        
        if not local_model_path.exists():
            print(f"Downloading model from MinIO: {MINIO_BUCKET}/{MINIO_MODEL_KEY}")
            if not minio_service.download_file(MINIO_MODEL_KEY, local_model_path):
                raise RuntimeError(f"Failed to download model from MinIO: {MINIO_MODEL_KEY}")
            print(f"Model downloaded to: {local_model_path}")
        else:
            print(f"Using cached model: {local_model_path}")
        
        # Use ONNX Runtime for inference
        from app.services.onnx_inference import ONNXYOLOSegmentation
        print(f"Loading ONNX model from {local_model_path}")
        model = ONNXYOLOSegmentation(str(local_model_path))
        print(f"ONNX model loaded successfully")
        
        # Inject model into controller
        app.controllers.api_controller.model = model
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

# Main UI (home)
@app.get("/", response_class=None)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Include routers
app.include_router(api_router)
app.include_router(gallery_router)

if __name__ == "__main__":
    import uvicorn
    Path("templates").mkdir(exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)