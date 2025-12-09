"""
ONNX Runtime Inference Service for YOLOv8 Segmentation

This module provides ONNX Runtime-based inference that matches the ultralytics API output format.
Enhanced with letterbox preprocessing for improved accuracy.
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
    Enhanced with letterbox preprocessing for improved accuracy.
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
        
        # Preprocess with letterbox (preserves aspect ratio)
        input_tensor, scale, pad = self._preprocess(image)
        
        # Inference
        outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        
        # Post-process (pass scale and pad for coordinate adjustment)
        result = self._postprocess(
            outputs,
            orig_shape=(orig_h, orig_w),
            conf_threshold=conf,
            iou_threshold=iou,
            scale=scale,
            pad=pad
        )
        
        return [result]
    
    def _letterbox(
        self,
        image: np.ndarray,
        new_shape: int = 640,
        color: Tuple[int, int, int] = (114, 114, 114),
        auto: bool = False,
        scaleFill: bool = False,
        scaleup: bool = True,
        stride: int = 32
    ) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """
        Resize and pad image while maintaining aspect ratio.
        
        This matches the Ultralytics letterbox implementation for consistent results.
        
        Args:
            image: Input image (BGR, HWC)
            new_shape: Target size
            color: Padding color (gray by default, matching Ultralytics)
            auto: Minimum rectangle
            scaleFill: Stretch to fill
            scaleup: Allow scaling up
            stride: Stride for padding alignment
        
        Returns:
            Tuple of (letterboxed image, scale ratio, (dw, dh) padding)
        """
        shape = image.shape[:2]  # current shape [height, width]
        
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)
        
        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        if not scaleup:  # only scale down, do not scale up
            r = min(r, 1.0)
        
        # Compute padding
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
        
        if auto:  # minimum rectangle
            dw, dh = np.mod(dw, stride), np.mod(dh, stride)
        elif scaleFill:  # stretch
            dw, dh = 0.0, 0.0
            new_unpad = (new_shape[1], new_shape[0])
            r = new_shape[1] / shape[1]
        
        dw /= 2  # divide padding into 2 sides
        dh /= 2
        
        if shape[::-1] != new_unpad:
            image = cv2.resize(image, new_unpad, interpolation=cv2.INTER_LINEAR)
        
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        image = cv2.copyMakeBorder(image, top, bottom, left, right, 
                                    cv2.BORDER_CONSTANT, value=color)
        
        return image, r, (dw, dh)
    
    def _preprocess(self, image: np.ndarray) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """
        Preprocess image for YOLO inference with letterbox padding.
        
        Returns:
            Tuple of (input tensor, scale ratio, (dw, dh) padding)
        """
        # Apply letterbox to maintain aspect ratio
        img, scale, pad = self._letterbox(image, self.img_size)
        
        # BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # HWC to CHW
        img = img.transpose(2, 0, 1)
        
        # Normalize to [0, 1]
        img = img.astype(np.float32) / 255.0
        
        # Add batch dimension
        img = np.expand_dims(img, axis=0)
        
        return img, scale, pad
    
    def _postprocess(
        self,
        outputs: List[np.ndarray],
        orig_shape: Tuple[int, int],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        scale: float = 1.0,
        pad: Tuple[float, float] = (0, 0)
    ) -> YOLOv8SegmentResult:
        """
        Post-process ONNX outputs to match ultralytics format.
        
        YOLOv8-seg output format:
        - output0: [1, 49, 8400] - boxes + class scores + mask coefficients
        - output1: [1, 32, 160, 160] - prototype masks
        
        Args:
            outputs: ONNX model outputs
            orig_shape: Original image shape (H, W)
            conf_threshold: Confidence threshold
            iou_threshold: IoU threshold for NMS
            scale: Scale ratio from letterbox
            pad: Padding (dw, dh) from letterbox
        """
        # Parse outputs based on YOLOv8-seg architecture
        if len(outputs) >= 2:
            # Segmentation model with masks
            predictions = outputs[0]  # [1, 49, 8400]
            proto_masks = outputs[1]  # [1, 32, 160, 160]
        else:
            # Detection only
            predictions = outputs[0]
            proto_masks = None
        
        # Process detections
        predictions = predictions[0].T  # [8400, 49]
        
        # Extract boxes, scores, and mask coefficients
        # Format: [x, y, w, h, class_scores..., mask_coeffs...]
        boxes = predictions[:, :4]  # [8400, 4] - x, y, w, h
        
        # Number of classes (49 - 4 - 32 = 13 for DeepFashion2)
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
        
        # Reverse letterbox transformation to get coordinates in original image space
        # 1. Remove padding offset
        boxes_xyxy[:, [0, 2]] -= pad[0]  # x coords
        boxes_xyxy[:, [1, 3]] -= pad[1]  # y coords
        
        # 2. Reverse scale
        boxes_xyxy /= scale
        
        # 3. Clip to original image bounds
        boxes_xyxy[:, [0, 2]] = np.clip(boxes_xyxy[:, [0, 2]], 0, orig_shape[1])
        boxes_xyxy[:, [1, 3]] = np.clip(boxes_xyxy[:, [1, 3]], 0, orig_shape[0])
        
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
                orig_shape,
                scale,
                pad
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
        orig_shape: Tuple[int, int],
        scale: float = 1.0,
        pad: Tuple[float, float] = (0, 0)
    ) -> np.ndarray:
        """
        Process prototype masks with coefficients to get instance masks.
        
        Args:
            proto_masks: [32, H, W] prototype masks
            mask_coeffs: [N, 32] mask coefficients
            orig_shape: Original image shape (H, W)
            scale: Scale ratio from letterbox
            pad: Padding (dw, dh) from letterbox
        
        Returns:
            Instance masks [N, H, W] in original image space
        """
        # Matrix multiplication: [N, 32] @ [32, H*W] -> [N, H*W]
        proto_h, proto_w = proto_masks.shape[1], proto_masks.shape[2]
        proto_flat = proto_masks.reshape(32, -1)  # [32, H*W]
        
        masks = np.matmul(mask_coeffs, proto_flat)  # [N, H*W]
        masks = masks.reshape(-1, proto_h, proto_w)  # [N, H, W]
        
        # Sigmoid activation
        masks = 1 / (1 + np.exp(-masks))
        
        # Scale masks back to letterboxed image size
        letterbox_h = int(self.img_size)
        letterbox_w = int(self.img_size)
        
        # First resize to letterbox size
        resized_masks = []
        for mask in masks:
            resized = cv2.resize(mask, (letterbox_w, letterbox_h))
            resized_masks.append(resized)
        masks = np.array(resized_masks)
        
        # Remove padding from masks
        pad_w, pad_h = int(pad[0]), int(pad[1])
        if pad_h > 0 or pad_w > 0:
            masks = masks[:, pad_h:letterbox_h-pad_h, pad_w:letterbox_w-pad_w]
        
        # Resize to original image size
        final_masks = []
        for mask in masks:
            resized = cv2.resize(mask, (orig_shape[1], orig_shape[0]))
            final_masks.append(resized)
        
        return np.array(final_masks)


# Convenience function for drop-in replacement
def load_onnx_model(model_path: str) -> ONNXYOLOSegmentation:
    """Load ONNX model - same interface as YOLO(model_path)."""
    return ONNXYOLOSegmentation(model_path)
