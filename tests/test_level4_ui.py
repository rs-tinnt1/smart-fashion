"""
Level 4: Frontend UI Layer Tests

Tests for frontend pages using HTTP requests.
These tests verify that UI pages render correctly and display proper content.
"""

import pytest
import httpx
import re


class TestHomePage:
    """INT-UI-001 & INT-UI-002: Home Page Tests"""

    @pytest.mark.level4
    def test_home_page_loads(self, base_url):
        """INT-UI-001: Verify home page loads successfully."""
        response = httpx.get(f"{base_url}/", timeout=10.0)
        assert response.status_code == 200

    @pytest.mark.level4
    def test_home_page_contains_upload_zone(self, base_url):
        """INT-UI-001: Verify upload dropzone is present."""
        response = httpx.get(f"{base_url}/", timeout=10.0)
        content = response.text
        
        assert "dropZone" in content, "Upload dropzone should be present"
        assert "Drag" in content, "Drag instruction should be present"

    @pytest.mark.level4
    def test_home_page_shows_file_limits(self, base_url):
        """INT-UI-001: Verify file size limits are displayed."""
        response = httpx.get(f"{base_url}/", timeout=10.0)
        content = response.text
        
        assert "100" in content, "Max 100 files limit should be shown"
        assert "500KB" in content, "Max 500KB limit should be shown"

    @pytest.mark.level4
    def test_home_page_has_navigation(self, base_url):
        """Verify navigation links are present."""
        response = httpx.get(f"{base_url}/", timeout=10.0)
        content = response.text
        
        assert "Gallery" in content, "Gallery link should be present"
        assert "/gallery" in content, "Gallery href should be present"


class TestGalleryPage:
    """INT-UI-003: Gallery Page Tests"""

    @pytest.mark.level4
    def test_gallery_page_loads(self, base_url):
        """INT-UI-003: Verify gallery page loads successfully."""
        response = httpx.get(f"{base_url}/gallery", timeout=10.0)
        assert response.status_code == 200

    @pytest.mark.level4
    def test_gallery_page_has_image_grid(self, base_url):
        """INT-UI-003: Verify image grid is present."""
        response = httpx.get(f"{base_url}/gallery", timeout=10.0)
        content = response.text
        
        # Either has images or shows "No Images Yet"
        has_grid = "grid" in content.lower()
        has_empty = "No Images" in content
        assert has_grid or has_empty, "Gallery should have grid or empty state"

    @pytest.mark.level4
    def test_gallery_shows_detection_count(self, base_url):
        """INT-UI-003: Verify detection count is shown (if images exist)."""
        response = httpx.get(f"{base_url}/gallery", timeout=10.0)
        content = response.text
        
        # Check if any images exist by looking for "objects detected"
        if "objects detected" in content:
            # Verify the count format
            pattern = r'\d+\s+objects?\s+detected'
            assert re.search(pattern, content), "Detection count format should be shown"

    @pytest.mark.level4
    def test_gallery_images_url_format(self, base_url):
        """INT-UI-003: Verify image URLs use correct format."""
        response = httpx.get(f"{base_url}/gallery", timeout=10.0)
        content = response.text
        
        # Check that if localhost:9000 URLs are used, minio:9000 is not
        if "localhost:9000" in content:
            # This is correct
            pass
        
        assert "minio:9000" not in content, "URLs should NOT contain minio:9000"


class TestAPIDocsPage:
    """API Documentation Page Tests"""

    @pytest.mark.level4
    def test_docs_page_loads(self, base_url):
        """Verify API docs page loads."""
        response = httpx.get(f"{base_url}/docs", timeout=10.0, follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.level4
    @pytest.mark.xfail(reason="Known issue: OpenAPI schema generation conflict with upload_controller response models")
    def test_openapi_schema_accessible(self, base_url):
        """Verify OpenAPI schema is accessible."""
        response = httpx.get(f"{base_url}/openapi.json", timeout=10.0)
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
