from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from app.config import UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR, MODEL_SEGMENT, LOCAL_MODEL_CACHE, S3_BUCKET
from app.controllers.segment_controller import router as api_router
from app.controllers.gallery_controller import router as gallery_router
from app.controllers.upload_controller import router as upload_router


# Global model and services
model = None
storage_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    global model, storage_service
    
    # Startup
    try:
        # Initialize S3/R2 storage service
        from app.services.storage_service import get_storage_service
        storage_service = get_storage_service()
        storage_service.ensure_bucket_exists()

        # Inject storage_service into segment_controller
        import app.controllers.segment_controller
        app.controllers.segment_controller.storage_service = storage_service
        
        # Download model from S3/R2
        LOCAL_MODEL_CACHE.mkdir(parents=True, exist_ok=True)
        local_model_path = LOCAL_MODEL_CACHE / MODEL_SEGMENT
        
        if not local_model_path.exists():
            print(f"Downloading model from S3/R2: {S3_BUCKET}/{MODEL_SEGMENT}")
            if not storage_service.download_file(MODEL_SEGMENT, local_model_path):
                raise RuntimeError(f"Failed to download model from S3/R2: {MODEL_SEGMENT}")
            print(f"Model downloaded to: {local_model_path}")
        else:
            print(f"Using cached model: {local_model_path}")
        
        # Load YOLO model (PyTorch .pt format)
        from app.services.inference_service import YOLOSegmentation
        print(f"Loading YOLO model from {local_model_path}")
        model = YOLOSegmentation(str(local_model_path))
        print(f"YOLO model loaded successfully")

        # Inject model into controller
        app.controllers.segment_controller.model = model
        
        # Initialize database connection pool
        from app.services.database_service import get_database
        db = await get_database()
        print("Database connection pool initialized")
        
    except Exception as e:
        print(f"Error during startup: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    try:
        from app.services.database_service import close_database
        await close_database()
        print("Database connection pool closed")
    except Exception as e:
        print(f"Error during shutdown: {e}")


app = FastAPI(
    title="Clothing Segmentation Web App",
    description="Web application for detecting and segmenting clothing items in images",
    version="2.0.0",
    lifespan=lifespan
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

from app.config import APP_VERSION

templates = Jinja2Templates(directory="templates")
templates.env.globals.update(APP_VERSION=APP_VERSION)


# Main UI (home)
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("pages/index.html", {"request": request})


# Include routers
app.include_router(api_router)
app.include_router(gallery_router)
app.include_router(upload_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    Path("templates").mkdir(exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
