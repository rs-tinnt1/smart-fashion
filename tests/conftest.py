"""
Pytest Configuration and Fixtures for Integration Tests

This module provides shared fixtures for all integration tests.
"""

import pytest
import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse

# Set environment variables for testing
os.environ.setdefault("DB_URL", "mysql://smartfashion:smartfashion@localhost:3306/smartfashion")
os.environ.setdefault("S3_ENDPOINT", "https://test.r2.cloudflarestorage.com")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_BUCKET", "smartfashion")
os.environ.setdefault("S3_REGION", "auto")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_image_path():
    """Return path to a test image file."""
    # Look for test images in inputs directory
    inputs_dir = Path(__file__).parent / "inputs"
    if inputs_dir.exists():
        images = list(inputs_dir.glob("*.png")) + list(inputs_dir.glob("*.jpg"))
        if images:
            return str(images[0])
    # Fallback: create a small test image
    return None


@pytest.fixture(scope="session")
def base_url():
    """Base URL for API tests."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def s3_endpoint():
    """S3/R2 endpoint for direct access tests."""
    return os.getenv("S3_ENDPOINT", "https://test.r2.cloudflarestorage.com")


@pytest.fixture
def db_credentials():
    """Database credentials for testing (parsed from DB_URL)."""
    db_url = os.getenv("DB_URL", "mysql://smartfashion:smartfashion@localhost:3306/smartfashion")
    parsed = urlparse(db_url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": parsed.username or "smartfashion",
        "password": parsed.password or "smartfashion",
        "database": parsed.path.lstrip("/") or "smartfashion",
    }


@pytest.fixture
def s3_credentials():
    """S3/R2 credentials for testing."""
    return {
        "endpoint": os.getenv("S3_ENDPOINT", "https://test.r2.cloudflarestorage.com"),
        "access_key": os.getenv("S3_ACCESS_KEY_ID", "test"),
        "secret_key": os.getenv("S3_SECRET_ACCESS_KEY", "test"),
        "bucket": os.getenv("S3_BUCKET", "smartfashion"),
    }
