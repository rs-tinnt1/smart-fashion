"""
S3 Storage Service for Smart Fashion Application

Provides S3-compatible client for storing/retrieving images and models.
Works with Cloudflare R2, AWS S3, MinIO, and other S3-compatible services.
"""

import io
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import (
    S3_ENDPOINT,
    S3_PUBLIC_ENDPOINT,
    S3_ACCESS_KEY_ID,
    S3_SECRET_ACCESS_KEY,
    S3_BUCKET,
    S3_REGION,
)


class StorageService:
    """S3-compatible client wrapper for file storage operations."""

    _instance: Optional["StorageService"] = None

    def __init__(self):
        # Configure boto3 for S3-compatible services (like R2)
        self.client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        )
        self.default_bucket = S3_BUCKET
        print(f"S3 client initialized: {S3_ENDPOINT}")

    @classmethod
    def get_instance(cls) -> "StorageService":
        """Get singleton instance of StorageService."""
        if cls._instance is None:
            cls._instance = StorageService()
        return cls._instance

    def ensure_bucket_exists(self, bucket_name: Optional[str] = None) -> bool:
        """Check if bucket exists (R2 doesn't support create_bucket via API)."""
        bucket = bucket_name or self.default_bucket
        try:
            self.client.head_bucket(Bucket=bucket)
            print(f"Bucket exists: {bucket}")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                print(f"Bucket not found: {bucket}. Please create it in Cloudflare dashboard.")
            else:
                print(f"Error checking bucket: {e}")
            return False

    def upload_file(
        self,
        local_path: str | Path,
        object_name: str,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> bool:
        """Upload a file from local path to S3/R2."""
        bucket = bucket_name or self.default_bucket
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self.client.upload_file(
                str(local_path),
                bucket,
                object_name,
                ExtraArgs=extra_args if extra_args else None,
            )
            print(f"Uploaded {local_path} -> {bucket}/{object_name}")
            return True
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return False

    def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Upload bytes directly to S3/R2."""
        bucket = bucket_name or self.default_bucket
        try:
            self.client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=io.BytesIO(data),
                ContentType=content_type,
            )
            print(f"Uploaded {len(data)} bytes -> {bucket}/{object_name}")
            return True
        except ClientError as e:
            print(f"Error uploading bytes: {e}")
            return False

    def download_file(
        self,
        object_name: str,
        local_path: str | Path,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Download a file from S3/R2 to local path."""
        bucket = bucket_name or self.default_bucket
        local_path = Path(local_path)

        # Create parent directories
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.client.download_file(bucket, object_name, str(local_path))
            print(f"Downloaded {bucket}/{object_name} -> {local_path}")
            return True
        except ClientError as e:
            print(f"Error downloading file: {e}")
            return False

    def download_bytes(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
    ) -> Optional[bytes]:
        """Download an object from S3/R2 directly into memory."""
        bucket = bucket_name or self.default_bucket
        try:
            response = self.client.get_object(Bucket=bucket, Key=object_name)
            return response["Body"].read()
        except ClientError as e:
            print(f"Error downloading bytes: {e}")
            return None

    def get_presigned_url(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
        expires_hours: int = 24,
    ) -> Optional[str]:
        """Get a presigned URL for accessing an object."""
        bucket = bucket_name or self.default_bucket
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": object_name},
                ExpiresIn=expires_hours * 3600,
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def get_public_url(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
        request_host: Optional[str] = None,
    ) -> str:
        """
        Get a direct public URL for accessing an object.
        For R2, this requires a custom domain or R2.dev subdomain to be configured.

        Args:
            object_name: Object key in S3/R2
            bucket_name: Optional bucket (defaults to configured bucket)
            request_host: Optional host from request header (not used for R2)
        """
        bucket = bucket_name or self.default_bucket

        if S3_PUBLIC_ENDPOINT:
            return f"{S3_PUBLIC_ENDPOINT.rstrip('/')}/{bucket}/{object_name}"

        # For R2 without a public custom domain, we must use presigned URLs
        # to ensure the browser can load the image without 403 Forbidden
        presigned_url = self.get_presigned_url(object_name, bucket)
        if presigned_url:
            return presigned_url

        # Fallback to direct URL
        return f"{S3_ENDPOINT}/{bucket}/{object_name}"

    def object_exists(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Check if an object exists in S3/R2."""
        bucket = bucket_name or self.default_bucket
        try:
            self.client.head_object(Bucket=bucket, Key=object_name)
            return True
        except ClientError:
            return False

    def delete_object(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """Delete an object from S3/R2."""
        bucket = bucket_name or self.default_bucket
        try:
            self.client.delete_object(Bucket=bucket, Key=object_name)
            print(f"Deleted {bucket}/{object_name}")
            return True
        except ClientError as e:
            print(f"Error deleting object: {e}")
            return False


# Convenient function to get service instance
def get_storage_service() -> StorageService:
    """Get the storage service singleton instance."""
    return StorageService.get_instance()
