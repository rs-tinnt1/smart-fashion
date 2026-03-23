from __future__ import annotations

import json
import uuid
from datetime import datetime

import pytest

from app.controllers import gallery_controller, segment_controller


class TestHealthEndpoint:
    def test_health_check_returns_200(self, test_client):
        response = test_client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_response_format(self, test_client):
        data = test_client.get("/api/health").json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
        assert data["model_name"] == "fake-seg.pt"

    def test_readiness_check_returns_ready(self, test_client):
        response = test_client.get("/api/readyz")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_liveness_check_returns_ok(self, test_client):
        response = test_client.get("/api/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_readiness_check_returns_503_when_storage_missing(self, test_client, monkeypatch):
        monkeypatch.setattr(segment_controller, "storage_service", None)
        response = test_client.get("/api/readyz")
        assert response.status_code == 503


class TestSegmentEndpoint:
    def test_segment_single_image(self, test_client, test_image_bytes, fake_db):
        response = test_client.post(
            "/api/segment",
            files={"files": ("sample.png", test_image_bytes, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["processed_images"] == 1
        assert len(data["results"]) == 1
        assert len(fake_db.images) == 1

    def test_segment_returns_file_id(self, test_client, test_image_bytes):
        result = test_client.post(
            "/api/segment",
            files={"files": ("sample.png", test_image_bytes, "image/png")},
        ).json()["results"][0]

        uuid.UUID(result["file_id"])

    def test_segment_saves_to_database(self, test_client, test_image_bytes):
        response = test_client.post(
            "/api/segment",
            files={"files": ("sample.png", test_image_bytes, "image/png")},
        )
        file_id = response.json()["results"][0]["file_id"]

        gallery = test_client.get("/api/gallery").json()
        image_ids = [img["id"] for img in gallery["images"]]
        assert file_id in image_ids

    def test_segment_presigned_url_format(self, test_client, test_image_bytes):
        result = test_client.post(
            "/api/segment",
            files={"files": ("sample.png", test_image_bytes, "image/png")},
        ).json()["results"][0]

        assert result["original_image_url"].startswith("https://example.test/")

    def test_reject_large_file(self, test_client):
        large_content = b"0" * (600 * 1024)
        response = test_client.post("/api/segment", files={"files": ("large.jpg", large_content, "image/jpeg")})

        assert response.status_code == 400
        assert "exceeds" in response.json()["detail"]

    def test_delete_image_endpoint(self, test_client, test_image_bytes, fake_storage):
        result = test_client.post(
            "/api/segment",
            files={"files": ("sample.png", test_image_bytes, "image/png")},
        ).json()["results"][0]

        response = test_client.delete(f"/api/delete/{result['file_id']}")

        assert response.status_code == 200
        assert fake_storage.objects == {}

    def test_delete_missing_image_returns_404(self, test_client):
        response = test_client.delete("/api/delete/missing-id")
        assert response.status_code == 404

    def test_stats_endpoint_returns_payload(self, test_client):
        response = test_client.get("/api/stats")
        assert response.status_code == 200
        assert response.json()["total_images"] == 0


class TestUploadAndJobEndpoints:
    def test_upload_creates_job(self, test_client, test_image_bytes, fake_db):
        response = test_client.post("/api/upload", files={"file": ("queued.png", test_image_bytes, "image/png")})
        data = response.json()

        assert response.status_code == 200
        assert data["status"] == "queued"
        assert data["image_id"] in fake_db.images
        assert data["job_id"] in fake_db.jobs

    def test_get_job_status(self, test_client, test_image_bytes):
        upload = test_client.post("/api/upload", files={"file": ("queued.png", test_image_bytes, "image/png")}).json()

        response = test_client.get(f"/api/jobs/{upload['job_id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_upload_rejects_non_image(self, test_client):
        response = test_client.post("/api/upload", files={"file": ("note.txt", b"hello", "text/plain")})
        assert response.status_code == 400

    def test_upload_rejects_large_file(self, test_client):
        response = test_client.post("/api/upload", files={"file": ("big.png", b"0" * (600 * 1024), "image/png")})
        assert response.status_code == 400

    def test_get_image_details(self, test_client, fake_db):
        image_id = "img-1"
        fake_db.images[image_id] = {
            "id": image_id,
            "storage_url": "uploads/img-1.png",
            "width": 20,
            "height": 10,
            "file_size": 123,
            "hash": None,
            "uploaded_at": datetime.utcnow(),
        }
        detection_id = awaitable_uuid(fake_db, image_id)

        response = test_client.get(f"/api/images/{image_id}")
        data = response.json()
        assert response.status_code == 200
        assert data["id"] == image_id
        assert data["detections"][0]["id"] == detection_id
        assert data["storage_url"].startswith("https://example.test/")

    def test_get_detection_details(self, test_client, fake_db):
        image_id = "img-2"
        fake_db.images[image_id] = {
            "id": image_id,
            "storage_url": "uploads/img-2.png",
            "width": 30,
            "height": 20,
            "file_size": 456,
            "hash": None,
            "uploaded_at": datetime.utcnow(),
        }
        detection_id = awaitable_uuid(fake_db, image_id)
        fake_db.polygons[detection_id] = {
            "id": "poly",
            "points_json": json.dumps([[{"x": 1, "y": 2}]]),
            "simplified": True,
        }
        fake_db.embeddings[detection_id] = {"id": "emb", "model_name": "demo", "vector": json.dumps([0.1] * 16)}

        response = test_client.get(f"/api/detections/{detection_id}")
        data = response.json()
        assert response.status_code == 200
        assert data["polygon"]["points"][0][0]["x"] == 1
        assert len(data["embedding"]) == 10

    def test_get_image_and_detection_404(self, test_client):
        assert test_client.get("/api/images/missing").status_code == 404
        assert test_client.get("/api/detections/missing").status_code == 404
        assert test_client.get("/api/jobs/missing").status_code == 404


class TestGalleryEndpoint:
    def test_gallery_returns_200(self, test_client):
        assert test_client.get("/api/gallery").status_code == 200

    def test_gallery_response_format(self, test_client):
        data = test_client.get("/api/gallery").json()
        assert "images" in data
        assert "count" in data

    def test_gallery_image_has_required_fields(self, test_client, test_image_bytes):
        test_client.post("/api/segment", files={"files": ("sample.png", test_image_bytes, "image/png")})
        image = test_client.get("/api/gallery").json()["images"][0]
        assert {"id", "original_url", "detection_count"}.issubset(image)

    def test_gallery_urls_do_not_use_minio(self, test_client, test_image_bytes):
        test_client.post("/api/segment", files={"files": ("sample.png", test_image_bytes, "image/png")})
        image = test_client.get("/api/gallery").json()["images"][0]
        assert "minio:9000" not in image["original_url"]

    def test_product_detail_and_gallery_image_api(self, test_client, test_image_bytes):
        result = test_client.post(
            "/api/segment", files={"files": ("sample.png", test_image_bytes, "image/png")}
        ).json()["results"][0]

        product = test_client.get(f"/product/{result['file_id']}")
        detail = test_client.get(f"/api/gallery/{result['file_id']}")
        asset = test_client.get(f"/api/gallery/{result['file_id']}/asset")
        crop = test_client.get(f"/api/detections/{detail.json()['detections'][0]['id']}/crop")

        assert product.status_code == 200
        assert detail.status_code == 200
        assert asset.status_code == 200
        assert crop.status_code == 200
        assert crop.headers["content-type"] == "image/png"
        assert detail.json()["id"] == result["file_id"]
        assert detail.json()["original_url"].startswith("https://example.test/")
        assert f"/api/gallery/{result['file_id']}/asset" in product.text
        assert "/api/detections/" in product.text

    def test_product_and_gallery_detail_404(self, test_client):
        assert test_client.get("/product/missing").status_code == 404
        assert test_client.get("/api/gallery/missing").status_code == 404
        assert test_client.get("/api/detections/missing/crop").status_code == 404

    def test_detection_crop_falls_back_to_bbox_when_polygon_missing(self, test_client, fake_db, fake_storage, test_image_bytes):
        image_id = "img-bbox-only"
        storage_key = "uploads/img-bbox-only.png"
        fake_storage.objects[storage_key] = test_image_bytes
        fake_db.images[image_id] = {
            "id": image_id,
            "storage_url": storage_key,
            "width": 32,
            "height": 32,
            "file_size": len(test_image_bytes),
            "hash": None,
            "uploaded_at": datetime.utcnow(),
        }
        detection_id = awaitable_uuid(fake_db, image_id)
        fake_db.polygons.pop(detection_id, None)

        response = test_client.get(f"/api/detections/{detection_id}/crop")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content

    def test_gallery_gracefully_handles_missing_database(self, test_client, monkeypatch):
        async def broken_db(*args, **kwargs):
            raise RuntimeError("db offline")

        monkeypatch.setattr(gallery_controller, "get_database", broken_db)
        response = test_client.get("/api/gallery")
        assert response.status_code == 200
        assert response.json()["available"] is False

    def test_product_detail_returns_503_when_db_missing(self, test_client, monkeypatch):
        async def broken_db(*args, **kwargs):
            raise RuntimeError("db offline")

        monkeypatch.setattr(gallery_controller, "get_database", broken_db)
        assert test_client.get("/product/some-id").status_code == 503
        assert test_client.get("/api/gallery/some-id").status_code == 503


def awaitable_uuid(fake_db, image_id: str) -> str:
    detection_id = str(uuid.uuid4())
    fake_db.detections[detection_id] = {
        "id": detection_id,
        "image_id": image_id,
        "label": "shirt",
        "confidence": 0.9,
        "bbox_x": 1,
        "bbox_y": 2,
        "bbox_w": 3,
        "bbox_h": 4,
    }
    return detection_id


class TestHelperFunctions:
    def test_build_detection_record_fills_bbox_from_contours(self):
        record = segment_controller._build_detection_record(
            {
                "class_name": "dress",
                "confidence": 0.5,
                "bbox": {"x": 0, "y": 0, "w": 0, "h": 0},
                "contours": [[{"x": 2, "y": 3}, {"x": 7, "y": 9}]],
            }
        )

        assert record["bbox_x"] == 2
        assert record["bbox_h"] == 6

    def test_load_model_on_demand_error_paths(self, monkeypatch):
        monkeypatch.setattr(segment_controller, "storage_service", None)
        with pytest.raises(Exception):
            segment_controller._load_model_on_demand(None)

        monkeypatch.setattr(segment_controller, "storage_service", object())
        monkeypatch.setattr(segment_controller, "model", None)

        def broken_loader(storage):
            raise RuntimeError("model fail")

        monkeypatch.setattr("app.services.inference_service.load_best_segment_model", broken_loader)
        with pytest.raises(Exception):
            segment_controller._load_model_on_demand(None)
