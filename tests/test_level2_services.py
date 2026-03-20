from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import database_service, inference_service, runtime_status, segmentation_service, storage_service


class DummyCursor:
    def __init__(self):
        self.executed: list[tuple[str, tuple]] = []
        self.executemany_calls: list[tuple[str, list[tuple]]] = []
        self.rowcount = 1

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, query, params=()):
        self.executed.append((query, params))

    async def executemany(self, query, rows):
        self.executemany_calls.append((query, list(rows)))

    async def fetchone(self):
        return {"ok": 1}

    async def fetchall(self):
        return []


class DummyConnection:
    def __init__(self, cursor: DummyCursor):
        self.cursor_obj = cursor
        self.begin_called = False
        self.commit_called = False
        self.rollback_called = False

    async def begin(self):
        self.begin_called = True

    async def commit(self):
        self.commit_called = True

    async def rollback(self):
        self.rollback_called = True

    def cursor(self, *args, **kwargs):
        return self.cursor_obj


class DummyAcquire:
    def __init__(self, conn: DummyConnection):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyPool:
    def __init__(self, conn: DummyConnection):
        self.conn = conn
        self.closed = False

    def acquire(self):
        return DummyAcquire(self.conn)

    def close(self):
        self.closed = True

    async def wait_closed(self):
        return None


class FakeYOLO:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.task = "segment"
        self.names = {0: "shirt"}

    def __call__(self, image, **kwargs):
        return [image]


class TestDatabaseService:
    def test_build_ssl_context_without_ssl(self, monkeypatch):
        monkeypatch.setattr(database_service, "DB_SSL", False)
        monkeypatch.setattr(database_service, "DB_SSL_MODE", "")
        assert database_service._build_ssl_context() is None

    @pytest.mark.asyncio
    async def test_get_instance_resets_after_failed_pool_init(self, monkeypatch):
        database_service.DatabaseService._instance = None

        async def broken_init(self):
            raise RuntimeError("boom")

        monkeypatch.setattr(database_service.DatabaseService, "_init_pool", broken_init)

        with pytest.raises(RuntimeError):
            await database_service.DatabaseService.get_instance()

        assert database_service.DatabaseService._instance is None

    @pytest.mark.asyncio
    async def test_create_image_with_detections_uses_transaction(self):
        cursor = DummyCursor()
        conn = DummyConnection(cursor)
        service = database_service.DatabaseService()
        setattr(service, "_pool", DummyPool(conn))

        detection = {
            "label": "shirt",
            "confidence": 0.95,
            "bbox_x": 1,
            "bbox_y": 2,
            "bbox_w": 3,
            "bbox_h": 4,
            "contours": [[{"x": 1, "y": 2}]],
            "simplified": True,
            "embedding": {"model_name": "demo", "vector": [0.1, 0.2]},
        }

        image_id = await service.create_image_with_detections(
            image_id="img-1",
            storage_url="uploads/img-1.png",
            width=20,
            height=10,
            file_size=99,
            hash="abc",
            detections=[detection],
        )

        assert image_id == "img-1"
        assert conn.begin_called is True
        assert conn.commit_called is True
        assert len(cursor.executed) == 1
        assert len(cursor.executemany_calls) == 3

    @pytest.mark.asyncio
    async def test_close_clears_pool(self):
        cursor = DummyCursor()
        conn = DummyConnection(cursor)
        service = database_service.DatabaseService()
        pool = DummyPool(conn)
        setattr(service, "_pool", pool)

        await service.close()

        assert pool.closed is True
        assert service._pool is None

    @pytest.mark.asyncio
    async def test_execute_fetch_and_transaction_helpers(self):
        cursor = DummyCursor()
        conn = DummyConnection(cursor)
        service = database_service.DatabaseService()
        setattr(service, "_pool", DummyPool(conn))

        await service.execute("SELECT 1", ())
        assert await service.fetch_one("SELECT 1", ()) == {"ok": 1}
        assert await service.fetch_all("SELECT 1", ()) == []

        async with service.transaction():
            pass

        assert conn.commit_called is True

    @pytest.mark.asyncio
    async def test_simple_create_methods_delegate_to_execute(self, monkeypatch):
        service = database_service.DatabaseService()
        calls = []

        async def fake_execute(query, params=()):
            calls.append((query, params))
            return 1

        monkeypatch.setattr(service, "execute", fake_execute)

        image_id = await service.create_image("img", "uploads/img.png", 1, 2, 3, None)
        job_id = await service.create_job("img")
        detection_id = await service.create_detection("img", "shirt", 0.9, 1, 2, 3, 4)
        polygon_id = await service.create_polygon("det", "[]", True)
        embedding_id = await service.create_embedding("det", "demo", "[0.1]")

        assert image_id == "img"
        assert all(identifier for identifier in [job_id, detection_id, polygon_id, embedding_id])
        assert len(calls) == 5

    @pytest.mark.asyncio
    async def test_get_image_with_detections_and_get_detection(self, monkeypatch):
        service = database_service.DatabaseService()

        async def fake_get_image(image_id):
            return {"id": image_id}

        async def fake_fetch_all(query, params=()):
            return [
                {"id": "det-1", "label": "shirt", "confidence": 0.8, "bbox_x": 1, "bbox_y": 2, "bbox_w": 3, "bbox_h": 4}
            ]

        async def fake_fetch_one(query, params=()):
            if "FROM detections" in query:
                return {
                    "id": "det-1",
                    "image_id": "img-1",
                    "label": "shirt",
                    "confidence": 0.8,
                    "bbox_x": 1,
                    "bbox_y": 2,
                    "bbox_w": 3,
                    "bbox_h": 4,
                }
            if "FROM polygons" in query:
                return {"points_json": "[]", "simplified": True}
            if "FROM embeddings" in query:
                return {"model_name": "demo", "vector": "[0.1]"}
            return None

        monkeypatch.setattr(service, "get_image", fake_get_image)
        monkeypatch.setattr(service, "fetch_all", fake_fetch_all)
        monkeypatch.setattr(service, "fetch_one", fake_fetch_one)

        image = await service.get_image_with_detections("img-1")
        detection = await service.get_detection("det-1")

        assert image is not None
        assert detection is not None
        assert image["detections"][0]["label"] == "shirt"
        assert detection["polygon"]["simplified"] is True

    @pytest.mark.asyncio
    async def test_atomic_pickup_job_marks_processing(self):
        cursor = DummyCursor()
        conn = DummyConnection(cursor)
        service = database_service.DatabaseService()
        setattr(service, "_pool", DummyPool(conn))

        async def fake_fetchone_once():
            return {"id": "job-1", "image_id": "img-1", "storage_url": "uploads/img.png"}

        setattr(cursor, "fetchone", fake_fetchone_once)

        job = await service.atomic_pickup_job()

        assert job is not None
        assert job["status"] == "processing"
        assert any("UPDATE jobs" in query for query, _ in cursor.executed)


class TestStorageService:
    def test_storage_service_upload_download_and_delete(self, monkeypatch):
        objects: dict[str, bytes] = {}

        class FakeClient:
            def put_object(self, Bucket, Key, Body, ContentType):
                objects[Key] = Body.read()

            def get_object(self, Bucket, Key):
                return {"Body": SimpleNamespace(read=lambda: objects[Key])}

            def generate_presigned_url(self, operation, Params, ExpiresIn):
                return f"https://signed.test/{Params['Key']}"

            def head_object(self, Bucket, Key):
                if Key not in objects:
                    raise storage_service.ClientError({"Error": {"Code": "404"}}, "head_object")

            def delete_object(self, Bucket, Key):
                objects.pop(Key, None)

            def head_bucket(self, Bucket):
                return None

            def download_file(self, Bucket, Key, Filename):
                Path(Filename).write_bytes(objects[Key])

        monkeypatch.setattr(storage_service.boto3, "client", lambda *args, **kwargs: FakeClient())
        storage = storage_service.StorageService()

        assert storage.ensure_bucket_exists() is True
        assert storage.upload_bytes(b"hello", "foo/bar.txt", "text/plain") is True
        assert storage.download_bytes("foo/bar.txt") == b"hello"
        presigned = storage.get_presigned_url("foo/bar.txt")
        assert presigned is not None
        assert presigned.startswith("https://signed.test/")
        assert storage.object_exists("foo/bar.txt") is True
        assert storage.delete_object("foo/bar.txt") is True

    def test_storage_service_prefers_public_endpoint_for_browser_urls(self, monkeypatch):
        monkeypatch.setattr(storage_service, "S3_PUBLIC_ENDPOINT", "http://localhost:9000")

        class PublicClient:
            def generate_presigned_url(self, operation, Params, ExpiresIn):
                return f"http://minio:9000/{Params['Bucket']}/{Params['Key']}?signed=1"

        monkeypatch.setattr(storage_service.boto3, "client", lambda *args, **kwargs: PublicClient())
        storage = storage_service.StorageService()

        assert storage.get_public_url("images/demo.png") == "http://localhost:9000/smartfashion/images/demo.png"

    def test_storage_service_error_and_fallback_paths(self, monkeypatch, tmp_path):
        monkeypatch.setattr(storage_service, "S3_PUBLIC_ENDPOINT", "")

        class BrokenClient:
            def head_bucket(self, Bucket):
                raise storage_service.ClientError({"Error": {"Code": "404"}}, "head_bucket")

            def upload_file(self, *args, **kwargs):
                raise storage_service.ClientError({"Error": {"Code": "500"}}, "upload_file")

            def put_object(self, *args, **kwargs):
                raise storage_service.ClientError({"Error": {"Code": "500"}}, "put_object")

            def get_object(self, *args, **kwargs):
                raise storage_service.ClientError({"Error": {"Code": "404"}}, "get_object")

            def generate_presigned_url(self, *args, **kwargs):
                raise storage_service.ClientError({"Error": {"Code": "500"}}, "generate_presigned_url")

            def head_object(self, *args, **kwargs):
                raise storage_service.ClientError({"Error": {"Code": "404"}}, "head_object")

            def delete_object(self, *args, **kwargs):
                raise storage_service.ClientError({"Error": {"Code": "500"}}, "delete_object")

            def download_file(self, *args, **kwargs):
                raise storage_service.ClientError({"Error": {"Code": "404"}}, "download_file")

        monkeypatch.setattr(storage_service.boto3, "client", lambda *args, **kwargs: BrokenClient())
        storage = storage_service.StorageService()

        file_path = tmp_path / "demo.txt"
        file_path.write_text("demo", encoding="utf-8")

        assert storage.ensure_bucket_exists() is False
        assert storage.upload_file(file_path, "demo.txt") is False
        assert storage.upload_bytes(b"demo", "demo.txt") is False
        assert storage.download_file("demo.txt", tmp_path / "copy.txt") is False
        assert storage.download_bytes("demo.txt") is None
        assert storage.get_public_url("demo.txt").endswith("/smartfashion/demo.txt")
        assert storage.object_exists("demo.txt") is False
        assert storage.delete_object("demo.txt") is False


class TestInferenceAndSegmentation:
    def test_load_model_from_cache(self, monkeypatch, tmp_path):
        monkeypatch.setattr(inference_service, "LOCAL_MODEL_CACHE", tmp_path)
        monkeypatch.setattr(
            inference_service,
            "YOLOSegmentation",
            lambda model_path, model_name=None: SimpleNamespace(model_name=model_name or Path(model_path).name),
        )

        storage = SimpleNamespace(
            download_file=lambda object_name, local_path: Path(local_path).write_bytes(b"weights") or True
        )

        model, model_name = inference_service.load_best_segment_model(storage)

        assert model_name == inference_service.MODEL_SEGMENT
        assert model.model_name == inference_service.MODEL_SEGMENT

    def test_load_model_retries_after_first_failure(self, monkeypatch, tmp_path):
        monkeypatch.setattr(inference_service, "LOCAL_MODEL_CACHE", tmp_path)
        calls = {"count": 0}

        class RetryModel:
            def __init__(self, model_path, model_name=None):
                calls["count"] += 1
                if calls["count"] == 1:
                    raise RuntimeError("bad cache")
                self.model_name = model_name

        monkeypatch.setattr(inference_service, "YOLOSegmentation", RetryModel)

        storage = SimpleNamespace(
            download_file=lambda object_name, local_path: Path(local_path).write_bytes(b"weights") or True
        )
        model = inference_service._load_cached_or_downloaded_model(storage, "retry.pt")

        assert model.model_name == "retry.pt"
        assert calls["count"] == 2

    def test_load_model_wrapper_uses_fake_yolo(self, monkeypatch, tmp_path):
        model_path = tmp_path / "demo.pt"
        model_path.write_bytes(b"weights")
        monkeypatch.setattr(inference_service, "YOLO", FakeYOLO)
        model = inference_service.load_model(str(model_path), model_name="demo.pt")
        assert model.model_name == "demo.pt"
        assert model.names[0] == "shirt"

    def test_runtime_status_helpers(self):
        app = SimpleNamespace(state=SimpleNamespace())
        runtime_status.initialize_runtime_state(app)
        runtime_status.set_runtime_component(app, "storage", True, "ok")
        runtime_status.add_runtime_warning(app, "warn")
        status, warnings = runtime_status.get_runtime_snapshot(app)

        assert status["storage"]["ready"] is True
        assert warnings == ["warn"]

    def test_segment_one_file_and_delete_output(self, fake_storage, test_image_bytes):
        model = segmentation_service.Any if False else None
        fake_model = __import__("tests.conftest", fromlist=["FakeModel"]).FakeModel(with_masks=True)

        result = segmentation_service.segment_one_file(
            image_bytes=test_image_bytes,
            filename="demo.png",
            content_type="image/png",
            model=fake_model,
            storage_service=fake_storage,
            request_host="localhost",
        )

        assert result["file_id"]
        image_key = str(result["original_image_key"])
        assert image_key.startswith("images/")
        deleted = segmentation_service.delete_output(result["file_id"], fake_storage, image_key)
        assert "original_image" in deleted
        assert "json" in deleted

    def test_process_one_image_detect_path_returns_polygon(self, monkeypatch, test_image_bytes):
        fake_model = __import__("tests.conftest", fromlist=["FakeModel"]).FakeModel(with_masks=False)

        monkeypatch.setattr(segmentation_service.cv2, "grabCut", lambda *args, **kwargs: None)

        result = segmentation_service._process_one_image(test_image_bytes, fake_model)

        assert result["json_data"]["objects"]
        assert result["json_data"]["objects"][0]["contours"]
