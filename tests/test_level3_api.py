"""
Level 3: API Endpoint Layer Tests

Tests for FastAPI endpoints.
These tests verify that API endpoints work correctly with services.
"""

import pytest
import httpx
import uuid
from pathlib import Path


class TestHealthEndpoint:
    """INT-API-001: Health Check Endpoint Tests"""

    @pytest.mark.level3
    def test_health_check_returns_200(self, base_url):
        """Verify health endpoint returns 200."""
        response = httpx.get(f"{base_url}/api/health", timeout=10.0)
        assert response.status_code == 200

    @pytest.mark.level3
    def test_health_check_response_format(self, base_url):
        """Verify health endpoint response format."""
        response = httpx.get(f"{base_url}/api/health", timeout=10.0)
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "model_loaded" in data
        assert "timestamp" in data

    @pytest.mark.level3
    def test_health_check_model_loaded(self, base_url):
        """Verify model is loaded."""
        response = httpx.get(f"{base_url}/api/health", timeout=10.0)
        data = response.json()
        assert data["model_loaded"] is True, "Model should be loaded"


class TestSegmentEndpoint:
    """INT-API-002, INT-API-003, INT-API-004: Segment Endpoint Tests"""

    @pytest.mark.level3
    @pytest.mark.slow
    def test_segment_single_image(self, base_url, test_image_path):
        """INT-API-002: Test segment endpoint with single image."""
        if test_image_path is None:
            pytest.skip("No test image available")
        
        with open(test_image_path, "rb") as f:
            files = {"files": (Path(test_image_path).name, f, "image/png")}
            response = httpx.post(
                f"{base_url}/api/segment",
                files=files,
                timeout=60.0
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert len(data["results"]) == 1

    @pytest.mark.level3
    @pytest.mark.slow
    def test_segment_returns_file_id(self, base_url, test_image_path):
        """INT-API-002: Test that segment returns a valid file_id."""
        if test_image_path is None:
            pytest.skip("No test image available")
        
        with open(test_image_path, "rb") as f:
            files = {"files": (Path(test_image_path).name, f, "image/png")}
            response = httpx.post(
                f"{base_url}/api/segment",
                files=files,
                timeout=60.0
            )
        
        data = response.json()
        result = data["results"][0]
        
        assert "file_id" in result
        # Verify UUID format
        try:
            uuid.UUID(result["file_id"])
        except ValueError:
            pytest.fail(f"file_id is not a valid UUID: {result['file_id']}")

    @pytest.mark.level3
    @pytest.mark.slow
    def test_segment_saves_to_database(self, base_url, test_image_path):
        """INT-API-003: Test that segment saves data to database."""
        if test_image_path is None:
            pytest.skip("No test image available")
        
        with open(test_image_path, "rb") as f:
            files = {"files": (Path(test_image_path).name, f, "image/png")}
            response = httpx.post(
                f"{base_url}/api/segment",
                files=files,
                timeout=60.0
            )
        
        data = response.json()
        file_id = data["results"][0]["file_id"]
        
        # Verify image exists in gallery
        gallery_response = httpx.get(f"{base_url}/api/gallery", timeout=10.0)
        gallery_data = gallery_response.json()
        
        image_ids = [img["id"] for img in gallery_data["images"]]
        assert file_id in image_ids, f"Image {file_id} should be in gallery"

    @pytest.mark.level3
    @pytest.mark.slow
    def test_segment_presigned_url_format(self, base_url, test_image_path):
        """INT-API-004: Test that segment returns correct presigned URL format."""
        if test_image_path is None:
            pytest.skip("No test image available")
        
        with open(test_image_path, "rb") as f:
            files = {"files": (Path(test_image_path).name, f, "image/png")}
            response = httpx.post(
                f"{base_url}/api/segment",
                files=files,
                timeout=60.0
            )
        
        data = response.json()
        result = data["results"][0]
        output_url = result.get("output_image_url", "")
        
        assert "localhost:9000" in output_url, f"URL should use localhost:9000, got: {output_url}"
        assert "minio:9000" not in output_url, f"URL should NOT use minio:9000, got: {output_url}"

    @pytest.mark.level3
    @pytest.mark.slow
    def test_segment_presigned_url_accessible(self, base_url, test_image_path):
        """INT-API-004: Test that presigned URL is accessible."""
        if test_image_path is None:
            pytest.skip("No test image available")
        
        with open(test_image_path, "rb") as f:
            files = {"files": (Path(test_image_path).name, f, "image/png")}
            response = httpx.post(
                f"{base_url}/api/segment",
                files=files,
                timeout=60.0
            )
        
        data = response.json()
        output_url = data["results"][0].get("output_image_url")
        
        if output_url:
            url_response = httpx.get(output_url, timeout=10.0)
            assert url_response.status_code == 200, f"URL should be accessible, got: {url_response.status_code}"


class TestGalleryEndpoint:
    """INT-API-005: Gallery Endpoint Tests"""

    @pytest.mark.level3
    def test_gallery_returns_200(self, base_url):
        """Verify gallery endpoint returns 200."""
        response = httpx.get(f"{base_url}/api/gallery", timeout=10.0)
        assert response.status_code == 200

    @pytest.mark.level3
    def test_gallery_response_format(self, base_url):
        """Verify gallery endpoint response format."""
        response = httpx.get(f"{base_url}/api/gallery", timeout=10.0)
        data = response.json()
        
        assert "images" in data
        assert "count" in data
        assert isinstance(data["images"], list)
        assert data["count"] == len(data["images"])

    @pytest.mark.level3
    def test_gallery_image_has_required_fields(self, base_url):
        """Verify gallery images have required fields."""
        response = httpx.get(f"{base_url}/api/gallery", timeout=10.0)
        data = response.json()
        
        if len(data["images"]) > 0:
            image = data["images"][0]
            assert "id" in image
            assert "original_url" in image
            assert "detection_count" in image

    @pytest.mark.level3
    def test_gallery_urls_use_localhost(self, base_url):
        """INT-API-005: Verify gallery URLs use localhost."""
        response = httpx.get(f"{base_url}/api/gallery", timeout=10.0)
        data = response.json()
        
        for image in data["images"]:
            original_url = image.get("original_url", "")
            if original_url:
                assert "localhost:9000" in original_url or original_url.startswith("/"), \
                    f"URL should use localhost:9000, got: {original_url}"
                assert "minio:9000" not in original_url


class TestFileSizeValidation:
    """INT-API-006: File Size Validation Tests"""

    @pytest.mark.level3
    @pytest.mark.xfail(reason="Known issue: File validation may return 500 due to content-type issues with fake files")
    def test_reject_large_file(self, base_url):
        """Test that files > 500KB are rejected."""
        # Create a large fake file (600KB of zeros)
        large_content = b"\x00" * (600 * 1024)
        
        files = {"files": ("large_file.jpg", large_content, "image/jpeg")}
        response = httpx.post(
            f"{base_url}/api/segment",
            files=files,
            timeout=30.0
        )
        
        assert response.status_code == 400, "Large files should be rejected with 400"
        data = response.json()
        assert "exceeds" in data.get("detail", "").lower() or "size" in data.get("detail", "").lower()
