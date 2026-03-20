import re
from pathlib import Path


class TestHomePage:
    def test_home_page_loads(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200

    def test_home_page_contains_upload_zone(self, test_client):
        content = test_client.get("/").text
        assert "dropZone" in content
        assert "Drag and drop" in content

    def test_home_page_shows_file_limits(self, test_client):
        content = test_client.get("/").text
        assert "100" in content
        assert "500KB" in content

    def test_home_page_has_navigation(self, test_client):
        content = test_client.get("/").text
        assert "Gallery" in content
        assert "/gallery" in content


class TestGalleryPage:
    def test_gallery_page_loads(self, test_client):
        response = test_client.get("/gallery")
        assert response.status_code == 200

    def test_gallery_page_has_image_grid(self, test_client, test_image_bytes):
        test_client.post("/api/segment", files={"files": ("sample.png", test_image_bytes, "image/png")})
        content = test_client.get("/gallery").text
        assert "gallery-grid" in content or "No Images Yet" in content

    def test_gallery_shows_detection_count(self, test_client, test_image_bytes):
        test_client.post("/api/segment", files={"files": ("sample.png", test_image_bytes, "image/png")})
        content = test_client.get("/gallery").text
        assert re.search(r"\d+\s+objects?\s+detected", content)

    def test_gallery_images_url_format(self, test_client, test_image_bytes):
        test_client.post("/api/segment", files={"files": ("sample.png", test_image_bytes, "image/png")})
        content = test_client.get("/gallery").text
        assert "minio:9000" not in content


class TestAPIDocsPage:
    def test_docs_page_loads(self, test_client):
        response = test_client.get("/docs", follow_redirects=True)
        assert response.status_code == 200

    def test_openapi_schema_accessible(self, test_client):
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestFrontendAssets:
    def test_base_template_exposes_app_version(self):
        content = Path("templates/layouts/base.html").read_text(encoding="utf-8")
        assert 'data-app-version="{{ APP_VERSION }}"' in content

    def test_image_processor_uses_detail_link_not_download(self):
        content = Path("static/js/modules/imageProcessor.js").read_text(encoding="utf-8")
        assert "View Details" in content
        assert "/product/${result.file_id}" in content
        assert "Download" not in content
