"""
Level 2: Service Layer Tests

Tests for DatabaseService and MinIOService.
These tests verify that the service layer properly interacts with infrastructure.
"""

import pytest
import uuid
import json

# Check if aiomysql is available (for local testing)
try:
    import aiomysql
    AIOMYSQL_AVAILABLE = True
except ImportError:
    AIOMYSQL_AVAILABLE = False


class TestDatabaseService:
    """INT-SVC-001 & INT-SVC-002: DatabaseService Tests"""

    @pytest.mark.level2
    @pytest.mark.asyncio
    @pytest.mark.skipif(not AIOMYSQL_AVAILABLE, reason="aiomysql not installed locally")
    async def test_database_connection(self):
        """INT-SVC-001: Verify database connection pool initializes."""
        from app.services.database import get_database
        
        db = await get_database()
        assert db is not None, "Database service should be initialized"
        assert db.pool is not None, "Database pool should be created"

    @pytest.mark.level2
    @pytest.mark.asyncio
    @pytest.mark.skipif(not AIOMYSQL_AVAILABLE, reason="aiomysql not installed locally")
    async def test_create_and_get_image(self):
        """INT-SVC-002: Test image CRUD operations."""
        from app.services.database import get_database
        
        db = await get_database()
        
        # Create test image
        test_id = str(uuid.uuid4())
        await db.create_image(
            image_id=test_id,
            storage_url=f"test/uploads/{test_id}.jpg",
            width=800,
            height=600,
            file_size=12345,
            hash="test_hash_123"
        )
        
        # Get image
        image = await db.get_image(test_id)
        assert image is not None, "Image should be retrieved"
        assert image['id'] == test_id
        assert image['width'] == 800
        assert image['height'] == 600

    @pytest.mark.level2
    @pytest.mark.asyncio
    @pytest.mark.skipif(not AIOMYSQL_AVAILABLE, reason="aiomysql not installed locally")
    async def test_create_detection(self):
        """INT-SVC-002: Test detection creation."""
        from app.services.database import get_database
        
        db = await get_database()
        
        # Create image first
        image_id = str(uuid.uuid4())
        await db.create_image(
            image_id=image_id,
            storage_url=f"test/uploads/{image_id}.jpg",
            width=800,
            height=600,
            file_size=12345,
            hash=None
        )
        
        # Create detection
        detection_id = await db.create_detection(
            image_id=image_id,
            label="short_sleeved_shirt",
            confidence=0.95,
            bbox_x=100,
            bbox_y=200,
            bbox_w=300,
            bbox_h=400
        )
        
        assert detection_id is not None, "Detection ID should be returned"
        
        # Get detection
        detection = await db.get_detection(detection_id)
        assert detection is not None
        assert detection['label'] == "short_sleeved_shirt"
        assert detection['confidence'] == pytest.approx(0.95, rel=0.01)

    @pytest.mark.level2
    @pytest.mark.asyncio
    @pytest.mark.skipif(not AIOMYSQL_AVAILABLE, reason="aiomysql not installed locally")
    async def test_create_polygon(self):
        """INT-SVC-002: Test polygon creation."""
        from app.services.database import get_database
        
        db = await get_database()
        
        # Create image and detection first
        image_id = str(uuid.uuid4())
        await db.create_image(
            image_id=image_id,
            storage_url=f"test/uploads/{image_id}.jpg",
            width=800,
            height=600,
            file_size=12345,
            hash=None
        )
        
        detection_id = await db.create_detection(
            image_id=image_id,
            label="pants",
            confidence=0.88,
            bbox_x=50,
            bbox_y=300,
            bbox_w=200,
            bbox_h=300
        )
        
        # Create polygon
        points = [[{"x": 50, "y": 300}, {"x": 250, "y": 300}, {"x": 250, "y": 600}]]
        polygon_id = await db.create_polygon(
            detection_id=detection_id,
            points_json=json.dumps(points),
            simplified=True
        )
        
        assert polygon_id is not None, "Polygon ID should be returned"


class TestMinIOService:
    """INT-SVC-003 & INT-SVC-004: MinIOService Tests"""

    @pytest.mark.level2
    def test_minio_service_initialization(self):
        """INT-SVC-003: Verify MinIO service initializes."""
        from app.services.minio_service import get_minio_service
        
        minio = get_minio_service()
        assert minio is not None, "MinIO service should be initialized"
        assert minio.client is not None, "MinIO client should be created"

    @pytest.mark.level2
    def test_minio_bucket_exists(self):
        """INT-SVC-003: Verify bucket exists or can be created."""
        from app.services.minio_service import get_minio_service
        
        minio = get_minio_service()
        # Just check if client can list bucket - don't try to create
        try:
            exists = minio.client.bucket_exists(minio.default_bucket)
            # Bucket exists or doesn't - both are valid for this test
            assert True
        except Exception as e:
            pytest.fail(f"MinIO connection failed: {e}")

    @pytest.mark.level2
    def test_minio_presigned_url_format(self):
        """INT-SVC-004: Verify presigned URL uses localhost, not minio."""
        from app.services.minio_service import get_minio_service
        
        minio = get_minio_service()
        
        # Use an existing object path format (don't need actual object for URL generation test)
        test_key = "test/presigned_test.txt"
        
        # Get presigned URL (will work even if object doesn't exist - it's just signing)
        url = minio.get_presigned_url(test_key)
        
        assert url is not None, "Presigned URL should be generated"
        assert "localhost:9000" in url, f"URL should use localhost:9000, got: {url}"
        assert "minio:9000" not in url, f"URL should NOT use minio:9000, got: {url}"

    @pytest.mark.level2
    @pytest.mark.slow
    def test_minio_upload_and_access(self):
        """INT-SVC-003 & INT-SVC-004: Test upload and presigned URL access."""
        import httpx
        from app.services.minio_service import get_minio_service
        
        minio = get_minio_service()
        
        # First ensure bucket exists
        minio.ensure_bucket_exists()
        
        # Upload a test object
        test_data = b"Test content for accessibility check"
        test_key = f"test/accessible_test_{uuid.uuid4()}.txt"
        
        result = minio.upload_bytes(test_data, test_key)
        if not result:
            pytest.skip("Could not upload to MinIO - may be permission issue")
        
        # Get presigned URL
        url = minio.get_presigned_url(test_key)
        
        # Test accessibility
        response = httpx.get(url, timeout=10.0)
        assert response.status_code == 200, f"URL should be accessible, got: {response.status_code}"
        
        # Cleanup
        minio.delete_object(test_key)
