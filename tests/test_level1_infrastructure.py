"""
Level 1: Infrastructure Layer Tests

Tests for MariaDB and MinIO infrastructure components.
These tests verify that the underlying services are properly configured.
"""

import pytest
import subprocess
import httpx


class TestMariaDBInfrastructure:
    """INT-INFRA-001: MariaDB Connection Tests"""

    @pytest.mark.level1
    def test_mariadb_container_running(self):
        """Verify MariaDB container is running."""
        result = subprocess.run(
            ["podman", "ps", "--filter", "name=mariadb", "--format", "{{.Status}}"],
            capture_output=True,
            text=True
        )
        assert "Up" in result.stdout, "MariaDB container is not running"

    @pytest.mark.level1
    def test_mariadb_healthcheck(self):
        """Verify MariaDB healthcheck passes."""
        result = subprocess.run(
            ["podman", "inspect", "--format", "{{.State.Health.Status}}", "mariadb"],
            capture_output=True,
            text=True
        )
        assert "healthy" in result.stdout.strip(), f"MariaDB is not healthy: {result.stdout}"

    @pytest.mark.level1
    def test_mariadb_tables_exist(self, db_credentials):
        """Verify required tables exist in database."""
        cmd = f"""podman exec mariadb mariadb -u{db_credentials['user']} -p{db_credentials['password']} {db_credentials['database']} -e "SHOW TABLES;" """
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        required_tables = ['images', 'jobs', 'detections', 'polygons', 'embeddings']
        for table in required_tables:
            assert table in result.stdout, f"Table '{table}' not found in database"


class TestMinIOInfrastructure:
    """INT-INFRA-002 & INT-INFRA-003: MinIO Connection Tests"""

    @pytest.mark.level1
    def test_minio_container_running(self):
        """Verify MinIO container is running."""
        result = subprocess.run(
            ["podman", "ps", "--filter", "name=minio", "--format", "{{.Status}}"],
            capture_output=True,
            text=True
        )
        assert "Up" in result.stdout, "MinIO container is not running"

    @pytest.mark.level1
    def test_minio_api_accessible(self, minio_url):
        """Verify MinIO API endpoint is accessible."""
        try:
            response = httpx.get(f"{minio_url}/minio/health/live", timeout=5.0)
            assert response.status_code == 200, f"MinIO health check failed: {response.status_code}"
        except httpx.ConnectError:
            pytest.fail("Cannot connect to MinIO API at localhost:9000")

    @pytest.mark.level1
    def test_minio_console_accessible(self, minio_console_url):
        """Verify MinIO Console is accessible."""
        try:
            response = httpx.get(minio_console_url, timeout=5.0, follow_redirects=True)
            assert response.status_code == 200, f"MinIO Console not accessible: {response.status_code}"
        except httpx.ConnectError:
            pytest.fail("Cannot connect to MinIO Console at localhost:9001")

    @pytest.mark.level1
    def test_minio_server_url_configured(self):
        """INT-INFRA-003: Verify MINIO_SERVER_URL is set correctly."""
        result = subprocess.run(
            ["podman", "exec", "minio", "env"],
            capture_output=True,
            text=True
        )
        assert "MINIO_SERVER_URL=http://localhost:9000" in result.stdout, \
            "MINIO_SERVER_URL is not configured correctly"

    @pytest.mark.level1
    def test_minio_bucket_exists(self, minio_credentials):
        """Verify smartfashion bucket exists."""
        cmd = f"""podman exec minio sh -c "mc alias set local http://localhost:9000 {minio_credentials['access_key']} {minio_credentials['secret_key']} && mc ls local/{minio_credentials['bucket']}" """
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        assert result.returncode == 0 or "does not exist" not in result.stderr, \
            f"Bucket {minio_credentials['bucket']} does not exist"
