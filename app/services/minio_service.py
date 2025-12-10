"""
MinIO Service for Smart Fashion Application

Provides real MinIO client for storing/retrieving images and models.
"""

import io
from pathlib import Path
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
from urllib.parse import urlparse

from app.config import (
    MINIO_ENDPOINT,
    MINIO_ROOT_USER,
    MINIO_ROOT_PASSWORD,
    MINIO_BUCKET,
    MINIO_REGION,
    MINIO_SECURE,
    MINIO_EXTERNAL_ENDPOINT,
)


class MinIOService:
    """MinIO client wrapper for file storage operations."""
    
    _instance: Optional["MinIOService"] = None
    
    def __init__(self):
        # Parse endpoint to get host:port
        endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
        
        self.client = Minio(
            endpoint,
            access_key=MINIO_ROOT_USER,
            secret_key=MINIO_ROOT_PASSWORD,
            secure=MINIO_SECURE,
            region=MINIO_REGION,
        )
        self.default_bucket = MINIO_BUCKET
        print(f"MinIO client initialized: {endpoint}")
    
    @classmethod
    def get_instance(cls) -> "MinIOService":
        """Get singleton instance of MinIOService."""
        if cls._instance is None:
            cls._instance = MinIOService()
        return cls._instance
    
    def ensure_bucket_exists(self, bucket_name: Optional[str] = None) -> bool:
        """Create bucket if it doesn't exist."""
        bucket = bucket_name or self.default_bucket
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket, location=MINIO_REGION)
                print(f"Created bucket: {bucket}")
            return True
        except S3Error as e:
            print(f"Error ensuring bucket exists: {e}")
            return False
    
    def upload_file(
        self,
        local_path: str | Path,
        object_name: str,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> bool:
        """Upload a file from local path to MinIO."""
        bucket = bucket_name or self.default_bucket
        try:
            self.client.fput_object(
                bucket,
                object_name,
                str(local_path),
                content_type=content_type,
            )
            print(f"Uploaded {local_path} -> {bucket}/{object_name}")
            return True
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return False
    
    def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Upload bytes directly to MinIO."""
        bucket = bucket_name or self.default_bucket
        try:
            self.client.put_object(
                bucket,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            print(f"Uploaded {len(data)} bytes -> {bucket}/{object_name}")
            return True
        except S3Error as e:
            print(f"Error uploading bytes: {e}")
            return False
    
    def download_file(
        self,
        object_name: str,
        local_path: str | Path,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Download a file from MinIO to local path."""
        bucket = bucket_name or self.default_bucket
        local_path = Path(local_path)
        
        # Create parent directories
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self.client.fget_object(bucket, object_name, str(local_path))
            print(f"Downloaded {bucket}/{object_name} -> {local_path}")
            return True
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return False
    
    def get_presigned_url(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
        expires_hours: int = 24,
    ) -> Optional[str]:
        """Get a presigned URL for accessing an object."""
        from datetime import timedelta
        bucket = bucket_name or self.default_bucket
        try:
            url = self.client.presigned_get_object(
                bucket,
                object_name,
                expires=timedelta(hours=expires_hours),
            )
            # Replace internal endpoint with external one for browser access
            internal_endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
            external_endpoint = MINIO_EXTERNAL_ENDPOINT.replace("http://", "").replace("https://", "")
            if internal_endpoint != external_endpoint:
                # Determine protocol from external endpoint
                protocol = "https://" if MINIO_EXTERNAL_ENDPOINT.startswith("https://") else "http://"
                url = url.replace(f"http://{internal_endpoint}", f"{protocol}{external_endpoint}")
                url = url.replace(f"https://{internal_endpoint}", f"{protocol}{external_endpoint}")
            return url
        except S3Error as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    def get_public_url(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
    ) -> str:
        """
        Get a direct public URL for accessing an object.
        Use this for public buckets where presigned signatures are not needed.
        """
        bucket = bucket_name or self.default_bucket
        # Use external endpoint for browser access
        return f"{MINIO_EXTERNAL_ENDPOINT}/{bucket}/{object_name}"
    
    def object_exists(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Check if an object exists in MinIO."""
        bucket = bucket_name or self.default_bucket
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False
    
    def delete_object(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Delete an object from MinIO."""
        bucket = bucket_name or self.default_bucket
        try:
            self.client.remove_object(bucket, object_name)
            print(f"Deleted {bucket}/{object_name}")
            return True
        except S3Error as e:
            print(f"Error deleting object: {e}")
            return False


# Convenient function to get service instance
def get_minio_service() -> MinIOService:
    """Get the MinIO service singleton instance."""
    return MinIOService.get_instance()
