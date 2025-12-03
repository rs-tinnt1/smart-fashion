# main.py  (your original file, trimmed)
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from ultralytics import YOLO
from app.config import UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR, MODEL_PATH
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

# MODEL loading
model = None
@app.on_event("startup")
async def load_model():
    global model
    try:
        model = YOLO(MODEL_PATH)
        print(f"Model loaded successfully from {MODEL_PATH}")
        # inject vào controller (giản lược)
        import app.controllers.api_controller
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