import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import APP_VERSION, MODEL_PRELOAD, STATIC_CACHE_CONTROL, STATIC_DIR, UVICORN_HOST, UVICORN_PORT
from app.controllers.gallery_controller import router as gallery_router
from app.controllers.segment_controller import router as api_router
from app.controllers.upload_controller import router as upload_router
from app.services.runtime_status import add_runtime_warning, initialize_runtime_state, set_runtime_component

# Global model and services
model = None
storage_service = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    global model, storage_service

    initialize_runtime_state(application)

    # Startup
    try:
        # Initialize S3/R2 storage service
        from app.services.storage_service import get_storage_service

        storage_service = get_storage_service()
        set_runtime_component(application, "storage", True, "client initialized")

        # Inject storage_service into segment_controller
        import app.controllers.segment_controller as segment_controller

        segment_controller.storage_service = storage_service

        if MODEL_PRELOAD:
            # Load YOLO model (PyTorch .pt format) when explicitly requested.
            from app.services.segmentation_service import preload_model

            try:
                _, loaded_model_name = preload_model(storage_service, application)
                print(f"YOLO model loaded successfully: {loaded_model_name}")
            except Exception as exc:
                warning = f"Model preload failed; continuing with on-demand loading: {exc}"
                print(warning)
                # Warning and component state are already set in preload_model
        else:
            print("Skipping model preload at startup (MODEL_PRELOAD=false)")
            set_runtime_component(application, "model", False, "deferred until first segmentation request")

        # Keep DB initialization lazy so Render health checks are not blocked by MySQL startup latency.
        set_runtime_component(application, "database", False, "deferred until first database request")

    except Exception as e:
        print(f"Error during startup: {e}")
        add_runtime_warning(application, f"Startup degraded: {e}")

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
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CacheControlledStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        if STATIC_CACHE_CONTROL:
            response.headers["Cache-Control"] = STATIC_CACHE_CONTROL
        return response


STATIC_DIR.mkdir(exist_ok=True)

if Path("static").exists():
    app.mount("/static", CacheControlledStaticFiles(directory="static"), name="static")

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
    uvicorn.run(app, host=UVICORN_HOST, port=UVICORN_PORT)
