from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from app.services.api import segment_one_file, delete_output, get_stats
from typing import List
from datetime import datetime

router = APIRouter()

model = None  # Để DI hoặc global model, sẽ gán trong main dạng include_router...

def get_model():
    global model
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return model

@router.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/api/segment")
async def segment_clothing(request: Request, files: List[UploadFile] = File(...), yolo_model=Depends(get_model)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    base_url = str(request.base_url).rstrip("/")
    results = []
    for file in files:
        try:
            result = segment_one_file(file, yolo_model, base_url)
            results.append(result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")
    return {"success": True, "processed_images": len(results), "results": results}

@router.delete("/api/outputs/{file_id}")
async def delete_output_endpoint(file_id: str):
    deleted = delete_output(file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Files not found")
    return {"success": True, "deleted": deleted}

@router.get("/api/stats")
async def get_stats_endpoint():
    return get_stats()
