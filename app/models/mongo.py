from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

class ImageObject(BaseModel):
    class_name: str
    confidence: float
    contours: List[List[Dict[str, int]]]
    color: Dict[str, int]
    label: Dict[str, Any]
    fill_alpha: float

class ImageMeta(BaseModel):
    id: str = Field(alias="_id")
    filename: str
    output_image: str
    json_file: str
    objects: List[ImageObject]
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    extra: Dict[str, Any] = {}

# Dùng để chuẩn bị insert/find với MongoDB
