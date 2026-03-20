"""
Background Worker for Smart Fashion Image Processing

Polls database for pending jobs and processes them using the YOLO model.
Run: python worker.py [--once]
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.database_service import DatabaseService, close_database, get_database
from app.services.inference_service import YOLOSegmentation, load_best_segment_model
from app.services.segmentation_service import _process_one_image
from app.services.storage_service import StorageService, get_storage_service


class Worker:
    """Background worker for processing image segmentation jobs."""

    def __init__(self):
        self.model: YOLOSegmentation | None = None
        self.model_name: str | None = None
        self.storage: StorageService | None = None
        self.db: DatabaseService | None = None
        self.running = True

    async def initialize(self):
        """Initialize worker dependencies."""
        print("Initializing worker...")

        # Initialize storage service
        self.storage = get_storage_service()

        # Download and load the configured model
        self.model, self.model_name = load_best_segment_model(self.storage)
        print(f"YOLO model loaded successfully: {self.model_name}")

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
        job_id = job["id"]
        image_id = job["image_id"]
        storage_url = job["storage_url"]

        print(f"Processing job {job_id} for image {image_id}")

        if self.storage is None or self.model is None or self.db is None:
            raise RuntimeError("Worker not initialized")

        try:
            # Download image bytes from storage
            image_bytes = self.storage.download_bytes(storage_url)
            if image_bytes is None:
                raise RuntimeError(f"Failed to download image: {storage_url}")

            segmentation = _process_one_image(image_bytes, self.model)
            export_data = segmentation["json_data"]
            detections_to_persist = []

            for obj in export_data.get("objects", []):
                bbox = obj.get("bbox") or {}
                detections_to_persist.append(
                    {
                        "label": obj.get("class_name", "unknown"),
                        "confidence": float(obj.get("confidence", 0.0)),
                        "bbox_x": int(bbox.get("x", 0)),
                        "bbox_y": int(bbox.get("y", 0)),
                        "bbox_w": int(bbox.get("w", 0)),
                        "bbox_h": int(bbox.get("h", 0)),
                        "contours": obj.get("contours", []),
                        "simplified": True,
                        "embedding": {"model_name": "placeholder", "vector": [0.0] * 128},
                    }
                )

            if detections_to_persist:
                await self.db.create_detections_batch(image_id, detections_to_persist)

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

    async def run(self, once: bool = False):
        """
        Main worker loop.

        Args:
            once: If True, process one job and exit
        """
        await self.initialize()

        if self.db is None:
            raise RuntimeError("Worker database not initialized")

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
