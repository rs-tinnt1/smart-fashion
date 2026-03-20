from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Keep tests local by default.
os.environ.setdefault("DB_URL", "mysql://smartfashion:smartfashion@localhost:3306/smartfashion")
os.environ.setdefault("S3_ENDPOINT", "https://test.r2.cloudflarestorage.com")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_BUCKET", "smartfashion")
os.environ.setdefault("S3_REGION", "auto")
os.environ.setdefault("MODEL_PRELOAD", "false")


def _build_test_image_bytes() -> bytes:
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    image[:, :] = (255, 255, 255)
    image[8:24, 10:22] = (20, 80, 200)
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("Failed to encode test image")
    return encoded.tobytes()


class FakeTensor:
    def __init__(self, values):
        self._values = np.array(values)

    def cpu(self):
        return self

    def numpy(self):
        return self._values


class FakeBoxes:
    def __init__(self, classes, confidences, boxes):
        self.cls = FakeTensor(classes)
        self.conf = FakeTensor(confidences)
        self.xyxy = FakeTensor(boxes)

    def __len__(self):
        return len(self._boxes())

    def _boxes(self):
        return self.xyxy.numpy()


class FakeMasks:
    def __init__(self, masks):
        self.data = FakeTensor(masks)


class FakeResult:
    def __init__(self, boxes, masks, names):
        self.boxes = boxes
        self.masks = masks
        self.names = names


class FakeModel:
    def __init__(self, with_masks: bool = True):
        self.task = "segment" if with_masks else "detect"
        self.names = {0: "shirt", 1: "pants", 2: "dress"}
        self.with_masks = with_masks

    def __call__(self, image, conf=0.25, iou=0.45, retina_masks=True, verbose=False):
        boxes = FakeBoxes(classes=[0], confidences=[0.93], boxes=[[4, 5, 26, 28]])
        masks = None
        if self.with_masks:
            mask = np.zeros((8, 8), dtype=np.float32)
            mask[1:7, 2:6] = 1.0
            masks = FakeMasks([mask])
        return [FakeResult(boxes=boxes, masks=masks, names=self.names)]


class FakeStorage:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def ensure_bucket_exists(self) -> bool:
        return True

    def upload_bytes(self, data: bytes, object_name: str, content_type: str = "application/octet-stream") -> bool:
        self.objects[object_name] = data
        return True

    def get_public_url(self, object_name: str, request_host: str | None = None) -> str:
        return f"https://example.test/{object_name}"

    def get_presigned_url(self, object_name: str, bucket_name: str | None = None, expires_hours: int = 24) -> str:
        return f"https://example.test/{object_name}?signed=1"

    def download_file(self, object_name: str, local_path: str | Path, bucket_name: str | None = None) -> bool:
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(self.objects.get(object_name, b"model"))
        return True

    def download_bytes(self, object_name: str, bucket_name: str | None = None) -> bytes | None:
        return self.objects.get(object_name)

    def object_exists(self, object_name: str, bucket_name: str | None = None) -> bool:
        return object_name in self.objects

    def delete_object(self, object_name: str, bucket_name: str | None = None) -> bool:
        self.objects.pop(object_name, None)
        return True


class FakeDB:
    def __init__(self):
        self.images: dict[str, dict] = {}
        self.jobs: dict[str, dict] = {}
        self.detections: dict[str, dict] = {}
        self.polygons: dict[str, dict] = {}
        self.embeddings: dict[str, dict] = {}

    async def fetch_one(self, query: str, params: tuple = ()):
        if "SELECT 1 AS ok" in query:
            return {"ok": 1}
        if "SELECT storage_url FROM images" in query:
            image = self.images.get(params[0])
            return {"storage_url": image["storage_url"]} if image else None
        return None

    async def fetch_all(self, query: str, params: tuple = ()):
        if "FROM images i" in query and "GROUP BY i.id" in query:
            rows = []
            for image in sorted(self.images.values(), key=lambda item: item["uploaded_at"], reverse=True):
                count = sum(1 for d in self.detections.values() if d["image_id"] == image["id"])
                rows.append({**image, "detection_count": count})
            limit = params[0] if params else len(rows)
            return rows[:limit]

        if "FROM detections WHERE image_id IN" in query:
            image_ids = set(params)
            labels = []
            for detection in self.detections.values():
                if detection["image_id"] in image_ids:
                    labels.append({"image_id": detection["image_id"], "label": detection["label"]})
            return labels

        if "FROM detections" in query and "WHERE image_id IN" in query:
            image_ids = set(params)
            return [d for d in self.detections.values() if d["image_id"] in image_ids]

        if "LEFT JOIN polygons" in query and "WHERE d.image_id = %s" in query:
            image_id = params[0]
            rows = []
            for detection in self.detections.values():
                if detection["image_id"] != image_id:
                    continue
                polygon = self.polygons.get(detection["id"])
                rows.append(
                    {
                        **detection,
                        "points_json": polygon["points_json"] if polygon else None,
                        "simplified": polygon["simplified"] if polygon else None,
                    }
                )
            return rows

        return []

    async def execute(self, query: str, params: tuple = ()) -> int:
        if query.startswith("DELETE FROM images"):
            image_id = params[0]
            self.images.pop(image_id, None)
            self.detections = {k: v for k, v in self.detections.items() if v["image_id"] != image_id}
            return 1
        if query.startswith("UPDATE jobs SET status = 'done'"):
            self.jobs[params[0]]["status"] = "done"
            self.jobs[params[0]]["completed_at"] = datetime.utcnow()
            return 1
        if query.startswith("UPDATE jobs SET status = 'error'"):
            self.jobs[params[1]]["status"] = "error"
            self.jobs[params[1]]["error_message"] = params[0]
            self.jobs[params[1]]["completed_at"] = datetime.utcnow()
            return 1
        return 1

    async def create_image(
        self, image_id: str, storage_url: str, width: int, height: int, file_size: int, hash: str | None
    ):
        self.images[image_id] = {
            "id": image_id,
            "storage_url": storage_url,
            "width": width,
            "height": height,
            "file_size": file_size,
            "hash": hash,
            "uploaded_at": datetime.utcnow(),
        }
        return image_id

    async def create_job(self, image_id: str):
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "image_id": image_id,
            "status": "pending",
            "error_message": None,
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
        }
        return job_id

    async def get_job(self, job_id: str):
        return self.jobs.get(job_id)

    async def get_image(self, image_id: str):
        return self.images.get(image_id)

    async def get_image_with_detections(self, image_id: str):
        image = self.images.get(image_id)
        if image is None:
            return None
        detections = [d for d in self.detections.values() if d["image_id"] == image_id]
        return {**image, "detections": detections}

    async def create_detection(
        self, image_id: str, label: str, confidence: float, bbox_x: int, bbox_y: int, bbox_w: int, bbox_h: int
    ):
        detection_id = str(uuid.uuid4())
        self.detections[detection_id] = {
            "id": detection_id,
            "image_id": image_id,
            "label": label,
            "confidence": confidence,
            "bbox_x": bbox_x,
            "bbox_y": bbox_y,
            "bbox_w": bbox_w,
            "bbox_h": bbox_h,
        }
        return detection_id

    async def create_polygon(self, detection_id: str, points_json: str, simplified: bool = False):
        polygon_id = str(uuid.uuid4())
        self.polygons[detection_id] = {
            "id": polygon_id,
            "points_json": points_json,
            "simplified": simplified,
        }
        return polygon_id

    async def create_embedding(self, detection_id: str, model_name: str, vector: str):
        embedding_id = str(uuid.uuid4())
        self.embeddings[detection_id] = {"id": embedding_id, "model_name": model_name, "vector": vector}
        return embedding_id

    async def create_detections_batch(self, image_id: str, detections: list[dict]):
        ids = []
        for detection in detections:
            detection_id = await self.create_detection(
                image_id=image_id,
                **{k: detection[k] for k in ["label", "confidence", "bbox_x", "bbox_y", "bbox_w", "bbox_h"]},
            )
            if detection.get("contours"):
                await self.create_polygon(
                    detection_id, json.dumps(detection["contours"]), detection.get("simplified", True)
                )
            if detection.get("embedding"):
                await self.create_embedding(
                    detection_id,
                    detection["embedding"]["model_name"],
                    json.dumps(detection["embedding"]["vector"]),
                )
            ids.append(detection_id)
        return ids

    async def create_image_with_detections(
        self,
        image_id: str,
        storage_url: str,
        width: int,
        height: int,
        file_size: int,
        hash: str | None,
        detections: list[dict],
    ):
        await self.create_image(image_id, storage_url, width, height, file_size, hash)
        await self.create_detections_batch(image_id, detections)
        return image_id

    async def get_detection(self, detection_id: str):
        detection = self.detections.get(detection_id)
        if detection is None:
            return None
        polygon = self.polygons.get(detection_id)
        embedding = self.embeddings.get(detection_id)
        return {**detection, "polygon": polygon, "embedding": embedding}

    async def atomic_pickup_job(self):
        for job in self.jobs.values():
            if job["status"] == "pending":
                job["status"] = "processing"
                job["started_at"] = datetime.utcnow()
                image = self.images[job["image_id"]]
                return {**job, "storage_url": image["storage_url"]}
        return None

    async def mark_job_done(self, job_id: str):
        await self.execute("UPDATE jobs SET status = 'done', completed_at = NOW() WHERE id = %s", (job_id,))

    async def mark_job_error(self, job_id: str, error_message: str):
        await self.execute(
            "UPDATE jobs SET status = 'error', error_message = %s, completed_at = NOW() WHERE id = %s",
            (error_message, job_id),
        )


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def test_image_bytes() -> bytes:
    return _build_test_image_bytes()


@pytest.fixture()
def test_image_path(tmp_path: Path, test_image_bytes: bytes) -> str:
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(test_image_bytes)
    return str(image_path)


@pytest.fixture()
def fake_db() -> FakeDB:
    return FakeDB()


@pytest.fixture()
def fake_storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture()
def base_url(test_client: TestClient) -> str:
    return str(test_client.base_url).rstrip("/")


@pytest.fixture()
def test_client(monkeypatch: pytest.MonkeyPatch, fake_db: FakeDB, fake_storage: FakeStorage) -> Iterator[TestClient]:
    import main
    from app.controllers import gallery_controller, segment_controller, upload_controller
    from app.services import storage_service
    from app.services import inference_service

    fake_model = FakeModel(with_masks=True)

    async def fake_get_database():
        return fake_db

    monkeypatch.setattr(storage_service, "get_storage_service", lambda: fake_storage)
    monkeypatch.setattr(inference_service, "load_best_segment_model", lambda storage: (fake_model, "fake-seg.pt"))
    monkeypatch.setattr(segment_controller, "storage_service", fake_storage)
    monkeypatch.setattr(segment_controller, "model", fake_model)
    monkeypatch.setattr(segment_controller, "model_name", "fake-seg.pt")
    monkeypatch.setattr(segment_controller, "get_database", fake_get_database)
    monkeypatch.setattr(upload_controller, "get_database", fake_get_database)
    monkeypatch.setattr(gallery_controller, "get_database", fake_get_database)
    monkeypatch.setattr(upload_controller, "get_storage_service", lambda: fake_storage)
    monkeypatch.setattr(gallery_controller, "get_storage_service", lambda: fake_storage)

    with TestClient(main.app) as client:
        yield client
