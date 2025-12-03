from app.models.s3 import S3Config, S3FileInfo
from typing import List, Optional

class S3Service:
    def __init__(self, config: S3Config):
        self.config = config
        # Kết nối S3 real (boto3, minio) về sau

    def upload_file(self, local_path: str, s3_key: str) -> S3FileInfo:
        # Upload file từ local lên S3
        return S3FileInfo(key=s3_key, url=f"https://fake_s3/{s3_key}")

    def list_files(self, prefix: str = "") -> List[S3FileInfo]:
        # List về sau
        return []

    def get_file_url(self, s3_key: str) -> str:
        return f"https://fake_s3/{s3_key}"
