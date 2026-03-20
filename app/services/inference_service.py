"""
PyTorch Inference Service for YOLO Segmentation

This module provides PyTorch-based inference using the ultralytics YOLO library.
Supports .pt model format for YOLOv8/YOLO11/YOLO26 segmentation models.
"""

from pathlib import Path
from typing import Any

from ultralytics.models.yolo.model import YOLO

from app.config import LOCAL_MODEL_CACHE, MODEL_SEGMENT, S3_BUCKET


class YOLOSegmentation:
    """
    YOLO Segmentation inference class using ultralytics library.

    Supports .pt (PyTorch) model format for YOLOv8 segmentation models.
    """

    def __init__(self, model_path: str, model_name: str | None = None):
        """
        Initialize YOLO model.

        Args:
            model_path: Path to .pt model file
            model_name: Optional model key/name for diagnostics
        """
        self.model_path = Path(model_path)
        self.model_name = model_name or self.model_path.name
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        print(f"Loading YOLO model from: {model_path}")

        # Hot-patch ultralytics to support custom Segment26 head for the fashion model
        try:
            import ultralytics.nn.modules.block as block_module
            import ultralytics.nn.modules.head as head_module

            if not hasattr(head_module, "Segment26") and hasattr(head_module, "Segment"):
                head_module.__dict__["Segment26"] = head_module.Segment

            if not hasattr(block_module, "Proto26") and hasattr(block_module, "Proto"):
                block_module.__dict__["Proto26"] = block_module.Proto
        except ImportError:
            pass

        self.model = YOLO(str(model_path))
        print("Model loaded successfully")
        print(f"  Loaded model: {self.model_name}")
        print(f"  Model type: {self.model.task}")
        print(f"  Class names: {list(self.model.names.values())[:5]}...")  # Show first 5 classes

    def __call__(self, image: Any, conf: float = 0.25, iou: float = 0.45, retina_masks: bool = True) -> list:
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
            verbose=False,  # Suppress per-image output
        )
        return results

    @property
    def names(self) -> dict:
        """Get class names mapping."""
        return self.model.names


def _download_model(storage_service: Any, model_name: str, local_model_path: Path) -> None:
    """Download a model from object storage to the local cache."""
    print(f"Downloading model from object storage: {S3_BUCKET}/{model_name}")
    if not storage_service.download_file(model_name, local_model_path):
        raise RuntimeError(f"Failed to download model from object storage: {model_name}")
    print(f"Model downloaded to: {local_model_path}")


def _load_cached_or_downloaded_model(storage_service: Any, model_name: str) -> YOLOSegmentation:
    """Load a model from cache, retrying once with a fresh download on failure."""
    local_model_path = LOCAL_MODEL_CACHE / model_name

    if local_model_path.exists():
        print(f"Using cached model: {local_model_path}")
    else:
        _download_model(storage_service, model_name, local_model_path)

    try:
        return YOLOSegmentation(str(local_model_path), model_name=model_name)
    except Exception as exc:
        print(f"Error loading model {model_name}: {exc}")
        print(f"Removing cached model: {local_model_path}")
        local_model_path.unlink(missing_ok=True)
        _download_model(storage_service, model_name, local_model_path)
        return YOLOSegmentation(str(local_model_path), model_name=model_name)


def load_best_segment_model(storage_service: Any) -> tuple[YOLOSegmentation, str]:
    """Load the configured segmentation model from object storage."""
    LOCAL_MODEL_CACHE.mkdir(parents=True, exist_ok=True)
    model = _load_cached_or_downloaded_model(storage_service, MODEL_SEGMENT)
    print(f"Active segmentation model: {MODEL_SEGMENT}")
    return model, MODEL_SEGMENT


def load_model(model_path: str, model_name: str | None = None) -> YOLOSegmentation:
    """Load YOLO model from path."""
    return YOLOSegmentation(model_path, model_name=model_name)
