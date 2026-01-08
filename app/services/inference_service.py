"""
PyTorch Inference Service for YOLO Segmentation

This module provides PyTorch-based inference using the ultralytics YOLO library.
Supports .pt model format for YOLOv8/YOLO11 segmentation models.
"""

from pathlib import Path
from typing import Any

from ultralytics import YOLO


class YOLOSegmentation:
    """
    YOLO Segmentation inference class using ultralytics library.
    
    Supports .pt (PyTorch) model format for YOLOv8/YOLO11 segmentation models.
    """
    
    def __init__(self, model_path: str):
        """
        Initialize YOLO model.
        
        Args:
            model_path: Path to .pt model file
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        print(f"Loading YOLO model from: {model_path}")
        self.model = YOLO(str(model_path))
        print(f"Model loaded successfully")
        print(f"  Model type: {self.model.task}")
        print(f"  Class names: {list(self.model.names.values())[:5]}...")  # Show first 5 classes
    
    def __call__(
        self,
        image: Any,
        conf: float = 0.25,
        iou: float = 0.45,
        retina_masks: bool = True
    ) -> list:
        """
        Run inference on image.
        
        Args:
            image: Input image (BGR, HWC format from cv2.imread or path string)
            conf: Confidence threshold
            iou: IoU threshold for NMS
            retina_masks: Whether to use high-resolution masks
        
        Returns:
            List of results from ultralytics YOLO
        """
        results = self.model(
            image,
            conf=conf,
            iou=iou,
            retina_masks=retina_masks,
            verbose=False  # Suppress per-image output
        )
        return results
    
    @property
    def names(self) -> dict:
        """Get class names mapping."""
        return self.model.names


def load_model(model_path: str) -> YOLOSegmentation:
    """Load YOLO model from path."""
    return YOLOSegmentation(model_path)
