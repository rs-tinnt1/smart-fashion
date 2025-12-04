"""
ONNX Runtime Inference Service for YOLOv8 Segmentation

This module provides ONNX Runtime-based inference that matches the ultralytics API output format.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import onnxruntime as ort


class ONNXSegmentationResult:
    """Wrapper class to match ultralytics result format."""
    
    def __init__(
        self,
        masks: Optional[np.ndarray],
        boxes: Dict[str, np.ndarray],
        names: Dict[int, str],
        orig_shape: Tuple[int, int]
    ):
        self.masks = masks
        self.boxes = boxes
        self.names = names
        self.orig_shape = orig_shape
    
    class MasksWrapper:
        def __init__(self, data: np.ndarray):
            self._data = data
        
        @property
        def data(self):
            return DataWrapper(self._data)
    
    class BoxesWrapper:
        def __init__(self, cls: np.ndarray, conf: np.ndarray, xyxy: np.ndarray):
            self._cls = cls
            self._conf = conf
            self._xyxy = xyxy
        
        @property
        def cls(self):
            return DataWrapper(self._cls)
        
        @property
        def conf(self):
            return DataWrapper(self._conf)
        
        @property
        def xyxy(self):
            return DataWrapper(self._xyxy)


class DataWrapper:
    """Wrapper to provide .cpu().numpy() interface like PyTorch tensors."""
    
    def __init__(self, data: np.ndarray):
        self._data = data
    
    def cpu(self):
        return self
    
    def numpy(self):
        return self._data


class YOLOv8SegmentResult:
    """Result class matching ultralytics YOLO result format."""
    
    def __init__(
        self,
        masks_data: Optional[np.ndarray],
        cls_data: np.ndarray,
        conf_data: np.ndarray,
        xyxy_data: np.ndarray,
        names: Dict[int, str]
    ):
        self._masks_data = masks_data
        self._cls_data = cls_data
        self._conf_data = conf_data
        self._xyxy_data = xyxy_data
        self.names = names
    
    @property
    def masks(self):
        if self._masks_data is None or len(self._masks_data) == 0:
            return None
        return ONNXSegmentationResult.MasksWrapper(self._masks_data)
    
    @property
    def boxes(self):
        return ONNXSegmentationResult.BoxesWrapper(
            self._cls_data,
            self._conf_data,
            self._xyxy_data
        )


class ONNXYOLOSegmentation:
    """
    ONNX Runtime inference class for YOLOv8 Segmentation models.
    
    Provides same interface as ultralytics.YOLO for easier drop-in replacement.
    """
    
    # DeepFashion2 class names (13 classes)
    DEFAULT_NAMES = {
        0: "short_sleeved_shirt",
        1: "long_sleeved_shirt",
        2: "short_sleeved_outwear",
        3: "long_sleeved_outwear",
        4: "vest",
        5: "sling",
        6: "shorts",
        7: "trousers",
        8: "skirt",
        9: "short_sleeved_dress",
        10: "long_sleeved_dress",
        11: "vest_dress",
        12: "sling_dress"
    }
    
    def __init__(self, model_path: str, providers: List[str] = None):
        """
        Initialize ONNX model.
        
        Args:
            model_path: Path to .onnx model file
            providers: ONNX execution providers (default: CPU)
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        # Default to CPU provider
        if providers is None:
            providers = ['CPUExecutionProvider']
        
        # Session options for optimization
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 4
        
        print(f"Loading ONNX model from: {model_path}")
        self.session = ort.InferenceSession(
            str(model_path),
            sess_options=sess_options,
            providers=providers
        )
        
        # Get model metadata
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.output_names = [o.name for o in self.session.get_outputs()]
        
        # Default input size from model
        self.img_size = self.input_shape[2] if len(self.input_shape) > 2 else 640
        
        print(f"Model loaded successfully")
        print(f"  Input: {self.input_name} {self.input_shape}")
        print(f"  Outputs: {self.output_names}")
    
    def __call__(
        self,
        image: np.ndarray,
        conf: float = 0.25,
        iou: float = 0.45,
        retina_masks: bool = True
    ) -> List[YOLOv8SegmentResult]:
        """
        Run inference on image.
        
        Args:
            image: Input image (BGR, HWC format from cv2.imread)
            conf: Confidence threshold
            iou: IoU threshold for NMS
            retina_masks: Whether to use high-resolution masks
        
        Returns:
            List of results matching ultralytics format
        """
        orig_h, orig_w = image.shape[:2]
        
        # Preprocess
        input_tensor = self._preprocess(image)
        
        # Inference
        outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        
        # Post-process
        result = self._postprocess(
            outputs,
            orig_shape=(orig_h, orig_w),
            conf_threshold=conf,
            iou_threshold=iou
        )
        
        return [result]
    
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for YOLO inference."""
        # Resize to model input size
        img = cv2.resize(image, (self.img_size, self.img_size))
        
        # BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # HWC to CHW
        img = img.transpose(2, 0, 1)
        
        # Normalize to [0, 1]
        img = img.astype(np.float32) / 255.0
        
        # Add batch dimension
        img = np.expand_dims(img, axis=0)
        
        return img
    
    def _postprocess(
        self,
        outputs: List[np.ndarray],
        orig_shape: Tuple[int, int],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45
    ) -> YOLOv8SegmentResult:
        """
        Post-process ONNX outputs to match ultralytics format.
        
        YOLOv8-seg output format:
        - output0: [1, 116, 8400] - boxes + class scores + mask coefficients
        - output1: [1, 32, 160, 160] - prototype masks
        """
        # Parse outputs based on YOLOv8-seg architecture
        if len(outputs) >= 2:
            # Segmentation model with masks
            predictions = outputs[0]  # [1, 116, 8400]
            proto_masks = outputs[1]  # [1, 32, 160, 160]
        else:
            # Detection only
            predictions = outputs[0]
            proto_masks = None
        
        # Process detections
        predictions = predictions[0].T  # [8400, 116]
        
        # Extract boxes, scores, and mask coefficients
        # Format: [x, y, w, h, class_scores..., mask_coeffs...]
        boxes = predictions[:, :4]  # [8400, 4] - x, y, w, h
        
        # Number of classes (116 - 4 - 32 = 80 for COCO, but DeepFashion2 has 13)
        num_mask_coeffs = 32 if proto_masks is not None else 0
        num_classes = predictions.shape[1] - 4 - num_mask_coeffs
        
        class_scores = predictions[:, 4:4 + num_classes]  # [8400, num_classes]
        mask_coeffs = predictions[:, 4 + num_classes:] if num_mask_coeffs > 0 else None
        
        # Get best class and confidence for each detection
        class_ids = np.argmax(class_scores, axis=1)
        confidences = np.max(class_scores, axis=1)
        
        # Filter by confidence threshold
        mask = confidences > conf_threshold
        boxes = boxes[mask]
        class_ids = class_ids[mask]
        confidences = confidences[mask]
        if mask_coeffs is not None:
            mask_coeffs = mask_coeffs[mask]
        
        if len(boxes) == 0:
            return YOLOv8SegmentResult(
                masks_data=None,
                cls_data=np.array([]),
                conf_data=np.array([]),
                xyxy_data=np.array([]),
                names=self.DEFAULT_NAMES
            )
        
        # Convert xywh to xyxy
        boxes_xyxy = self._xywh_to_xyxy(boxes)
        
        # Scale boxes to original image size
        scale_x = orig_shape[1] / self.img_size
        scale_y = orig_shape[0] / self.img_size
        boxes_xyxy[:, [0, 2]] *= scale_x
        boxes_xyxy[:, [1, 3]] *= scale_y
        
        # Apply NMS
        keep_indices = self._nms(boxes_xyxy, confidences, iou_threshold)
        
        boxes_xyxy = boxes_xyxy[keep_indices]
        class_ids = class_ids[keep_indices]
        confidences = confidences[keep_indices]
        if mask_coeffs is not None:
            mask_coeffs = mask_coeffs[keep_indices]
        
        # Process masks
        masks_data = None
        if proto_masks is not None and mask_coeffs is not None and len(mask_coeffs) > 0:
            masks_data = self._process_masks(
                proto_masks[0],  # [32, 160, 160]
                mask_coeffs,      # [N, 32]
                orig_shape
            )
        
        return YOLOv8SegmentResult(
            masks_data=masks_data,
            cls_data=class_ids.astype(np.float32),
            conf_data=confidences.astype(np.float32),
            xyxy_data=boxes_xyxy.astype(np.float32),
            names=self.DEFAULT_NAMES
        )
    
    def _xywh_to_xyxy(self, boxes: np.ndarray) -> np.ndarray:
        """Convert boxes from [x_center, y_center, w, h] to [x1, y1, x2, y2]."""
        xyxy = np.zeros_like(boxes)
        xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2  # x1
        xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2  # y1
        xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2  # x2
        xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2  # y2
        return xyxy
    
    def _nms(
        self,
        boxes: np.ndarray,
        scores: np.ndarray,
        iou_threshold: float
    ) -> np.ndarray:
        """Non-Maximum Suppression."""
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            if order.size == 1:
                break
            
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            iou = inter / (areas[i] + areas[order[1:]] - inter)
            
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        return np.array(keep)
    
    def _process_masks(
        self,
        proto_masks: np.ndarray,
        mask_coeffs: np.ndarray,
        orig_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Process prototype masks with coefficients to get instance masks.
        
        Args:
            proto_masks: [32, H, W] prototype masks
            mask_coeffs: [N, 32] mask coefficients
            orig_shape: Original image shape (H, W)
        
        Returns:
            Instance masks [N, H, W]
        """
        # Matrix multiplication: [N, 32] @ [32, H*W] -> [N, H*W]
        proto_h, proto_w = proto_masks.shape[1], proto_masks.shape[2]
        proto_flat = proto_masks.reshape(32, -1)  # [32, H*W]
        
        masks = np.matmul(mask_coeffs, proto_flat)  # [N, H*W]
        masks = masks.reshape(-1, proto_h, proto_w)  # [N, H, W]
        
        # Sigmoid activation
        masks = 1 / (1 + np.exp(-masks))
        
        # Resize masks to original image size
        resized_masks = []
        for mask in masks:
            resized = cv2.resize(mask, (orig_shape[1], orig_shape[0]))
            resized_masks.append(resized)
        
        return np.array(resized_masks)


# Convenience function for drop-in replacement
def load_onnx_model(model_path: str) -> ONNXYOLOSegmentation:
    """Load ONNX model - same interface as YOLO(model_path)."""
    return ONNXYOLOSegmentation(model_path)
