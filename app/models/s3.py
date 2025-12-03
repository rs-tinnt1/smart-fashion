from pydantic import BaseModel
from typing import Optional

class S3Config(BaseModel):
    bucket: str
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    region_name: Optional[str] = None

class S3FileInfo(BaseModel):
    key: str
    url: str
    etag: Optional[str]
    size: Optional[int]
    content_type: Optional[str]
