"""
Level 1: Infrastructure Layer Tests

Tests for MariaDB infrastructure components.
Note: MinIO tests have been removed as we now use Cloudflare R2 (cloud storage).
R2 connectivity is tested at the service layer (Level 2).
"""

import pytest
import subprocess


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
