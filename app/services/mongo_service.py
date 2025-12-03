from app.models.mongo import ImageMeta
from typing import Any, List

# TODO: Phần này sẽ dùng pymongo/motor để actual implement
# Hiện tại stub để service CI chạy trước
class MongoService:
    def __init__(self):
        # Khởi tạo MongoDB client ở đây hoặc inject vào (kết nối thật sau)
        pass

    def insert_image(self, meta: ImageMeta) -> Any:
        # Thêm dữ liệu image vào mongo
        pass

    def find_images(self, limit: int = 10) -> List[ImageMeta]:
        # Lấy danh sách ảnh, ví dụ dùng cho gallery
        return []  # Stub

    def get_image(self, image_id: str) -> ImageMeta:
        pass

    def delete_image(self, image_id: str) -> bool:
        pass
