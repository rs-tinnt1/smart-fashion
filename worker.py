"""
Background Worker for Smart Fashion Image Processing

Polls database for pending jobs and processes them using the ONNX model.
Run: python worker.py [--once]
"""

import asyncio
import sys
import json
import traceback
from pathlib import Path

import cv2
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import (
    LOCAL_MODEL_CACHE, MINIO_MODEL_KEY, MINIO_BUCKET, COLORS
)
from app.services.database_service import get_database, close_database
from app.services.storage_service import get_minio_service
from app.services.inference_service import ONNXYOLOSegmentation


class Worker:
    """Background worker for processing image segmentation jobs."""
    
    def __init__(self):
        self.model = None
        self.minio = None
        self.db = None
        self.running = True
    
    async def initialize(self):
        """Initialize worker dependencies."""
        print("Initializing worker...")
        
        # Initialize MinIO
        self.minio = get_minio_service()
        self.minio.ensure_bucket_exists()
        
        # Download and load model
        LOCAL_MODEL_CACHE.mkdir(parents=True, exist_ok=True)
        local_model_path = LOCAL_MODEL_CACHE / MINIO_MODEL_KEY
        
        if not local_model_path.exists():
            print(f"Downloading model from MinIO: {MINIO_BUCKET}/{MINIO_MODEL_KEY}")
            if not self.minio.download_file(MINIO_MODEL_KEY, local_model_path):
                raise RuntimeError(f"Failed to download model from MinIO: {MINIO_MODEL_KEY}")
            print(f"Model downloaded to: {local_model_path}")
        else:
            print(f"Using cached model: {local_model_path}")
        
        print(f"Loading ONNX model from {local_model_path}")
        self.model = ONNXYOLOSegmentation(str(local_model_path))
        print("ONNX model loaded successfully")
        
        # Initialize database
        self.db = await get_database()
        print("Worker initialized successfully")
    
    async def shutdown(self):
        """Cleanup worker resources."""
        print("Shutting down worker...")
        await close_database()
        print("Worker shutdown complete")
    
    async def process_job(self, job: dict) -> bool:
        """
        Process a single job.
        
        Args:
            job: Job dict with id, image_id, storage_url
            
        Returns:
            True if successful, False otherwise
        """
        job_id = job['id']
        image_id = job['image_id']
        storage_url = job['storage_url']
        
        print(f"Processing job {job_id} for image {image_id}")
        
        try:
            # Download image from MinIO
            temp_path = Path(f"/tmp/worker_{image_id}.jpg")
            if not self.minio.download_file(storage_url, temp_path):
                raise RuntimeError(f"Failed to download image: {storage_url}")
            
            # Load image
            image = cv2.imread(str(temp_path))
            if image is None:
                raise ValueError(f"Could not load image: {temp_path}")
            
            img_height, img_width = image.shape[:2]
            
            # Run inference
            results = self.model(image, conf=0.25, iou=0.45, retina_masks=True)
            
            # Process results
            if results[0].masks is not None:
                masks = results[0].masks.data.cpu().numpy()
                class_ids = results[0].boxes.cls.cpu().numpy()
                confidences = results[0].boxes.conf.cpu().numpy()
                boxes_xyxy = results[0].boxes.xyxy.cpu().numpy()
                class_names = results[0].names
                
                for i, mask in enumerate(masks):
                    # Get detection info
                    class_id = int(class_ids[i])
                    class_name = class_names[class_id]
                    confidence = float(confidences[i])
                    
                    # Get bounding box
                    bbox = boxes_xyxy[i]
                    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                    bbox_x, bbox_y = x1, y1
                    bbox_w, bbox_h = x2 - x1, y2 - y1
                    
                    # Process mask to get contours
                    contours_data = self._process_mask(
                        mask, img_width, img_height,
                        x1, y1, x2, y2
                    )
                    
                    # Create detection record
                    detection_id = await self.db.create_detection(
                        image_id=image_id,
                        label=class_name,
                        confidence=confidence,
                        bbox_x=bbox_x,
                        bbox_y=bbox_y,
                        bbox_w=bbox_w,
                        bbox_h=bbox_h
                    )
                    
                    # Create polygon record
                    if contours_data:
                        await self.db.create_polygon(
                            detection_id=detection_id,
                            points_json=json.dumps(contours_data),
                            simplified=True
                        )
                    
                    # Create stub embedding (placeholder - can integrate real embedding model later)
                    embedding_vector = [0.0] * 128  # Placeholder 128-dim embedding
                    await self.db.create_embedding(
                        detection_id=detection_id,
                        model_name="placeholder",
                        vector=json.dumps(embedding_vector)
                    )
                    
                    print(f"  Created detection: {class_name} ({confidence:.2f})")
            
            # Cleanup temp file
            temp_path.unlink(missing_ok=True)
            
            # Mark job as done
            await self.db.mark_job_done(job_id)
            print(f"Job {job_id} completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"Job {job_id} failed: {error_msg}")
            traceback.print_exc()
            await self.db.mark_job_error(job_id, error_msg)
            return False
    
    def _process_mask(
        self,
        mask: np.ndarray,
        img_width: int,
        img_height: int,
        x1: int, y1: int, x2: int, y2: int
    ) -> list:
        """
        Process a mask to extract polygon contours.
        
        Uses the same V5 mask processing logic from api.py.
        """
        # Expand bbox slightly (5% each side)
        bbox_margin = 0.05
        bbox_w = x2 - x1
        bbox_h = y2 - y1
        x1 = max(0, int(x1 - bbox_w * bbox_margin))
        y1 = max(0, int(y1 - bbox_h * bbox_margin))
        x2 = min(img_width, int(x2 + bbox_w * bbox_margin))
        y2 = min(img_height, int(y2 + bbox_h * bbox_margin))
        
        # Step 1: Resize mask
        mask_resized = cv2.resize(mask, (img_width, img_height),
                                  interpolation=cv2.INTER_LINEAR)
        
        # Step 2: Apply bounding box constraint
        bbox_mask = np.zeros_like(mask_resized)
        bbox_mask[y1:y2, x1:x2] = 1.0
        mask_resized = mask_resized * bbox_mask
        
        # Step 3: High threshold (0.75)
        MASK_THRESHOLD = 0.75
        mask_binary = (mask_resized > MASK_THRESHOLD).astype(np.uint8) * 255
        
        # Step 4: Morphological operations
        kernel_size = max(5, int(min(img_width, img_height) * 0.01))
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_OPEN, kernel, iterations=2)
        mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Step 5: Gaussian blur
        blur_size = max(3, kernel_size - 2)
        if blur_size % 2 == 0:
            blur_size += 1
        mask_binary = cv2.GaussianBlur(mask_binary, (blur_size, blur_size), 0)
        
        # Step 6: Final threshold
        _, mask_binary = cv2.threshold(mask_binary, 127, 255, cv2.THRESH_BINARY)
        
        # Step 7: Find contours
        contours, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        # Step 8: Filter and simplify contours
        if not contours:
            return []
        
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        largest = contours[0]
        largest_area = cv2.contourArea(largest)
        
        MIN_RATIO = 0.20
        filtered = [largest]
        for cnt in contours[1:]:
            if cv2.contourArea(cnt) >= largest_area * MIN_RATIO:
                filtered.append(cnt)
        
        # Douglas-Peucker approximation
        smoothed_contours = []
        for contour in filtered:
            epsilon = 0.001 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            smoothed_contours.append(approx)
        
        # Convert to JSON-serializable format
        contours_data = [
            [{"x": int(p[0][0]), "y": int(p[0][1])} for p in contour]
            for contour in smoothed_contours
        ]
        
        return contours_data
    
    async def run(self, once: bool = False):
        """
        Main worker loop.
        
        Args:
            once: If True, process one job and exit
        """
        await self.initialize()
        
        print("Worker started, polling for jobs...")
        
        try:
            while self.running:
                # Try to pick up a job atomically
                job = await self.db.atomic_pickup_job()
                
                if job:
                    await self.process_job(job)
                    if once:
                        break
                else:
                    if once:
                        print("No pending jobs found")
                        break
                    # Sleep before next poll
                    await asyncio.sleep(2)
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            await self.shutdown()


async def main():
    """Entry point for worker script."""
    once = "--once" in sys.argv
    worker = Worker()
    await worker.run(once=once)


if __name__ == "__main__":
    asyncio.run(main())
