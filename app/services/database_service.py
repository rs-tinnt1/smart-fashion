"""
MariaDB Database Service for Smart Fashion Application

Provides async connection pool and CRUD operations using aiomysql.
"""

from __future__ import annotations

import json
import ssl
import uuid
from contextlib import asynccontextmanager
from typing import Any

import aiomysql

from app.config import (
    DB_CONNECT_TIMEOUT,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_SSL,
    DB_SSL_CA,
    DB_SSL_CERT,
    DB_SSL_KEY,
    DB_SSL_MODE,
    DB_USER,
)


def _build_ssl_context() -> ssl.SSLContext | None:
    """Build SSL context for managed MySQL providers when required."""
    if not DB_SSL and not DB_SSL_MODE:
        return None

    ssl_mode = DB_SSL_MODE or "required"
    context = ssl.create_default_context()

    if DB_SSL_CA:
        context.load_verify_locations(cafile=DB_SSL_CA)

    if ssl_mode in {"required", "preferred"} and not DB_SSL_CA:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    if DB_SSL_CERT and DB_SSL_KEY:
        context.load_cert_chain(certfile=DB_SSL_CERT, keyfile=DB_SSL_KEY)

    return context


class DatabaseService:
    """Async MariaDB connection pool manager."""

    _instance = None
    _pool: aiomysql.Pool | None = None

    @classmethod
    async def get_instance(cls) -> DatabaseService:
        """Get singleton instance of DatabaseService."""
        if cls._instance is None:
            cls._instance = DatabaseService()
            await cls._instance._init_pool()
        instance = cls._instance
        if instance is None:
            raise RuntimeError("Database service failed to initialize")
        return instance

    async def _init_pool(self):
        """Initialize connection pool."""
        if self._pool is None:
            pool_kwargs = {
                "host": DB_HOST,
                "port": DB_PORT,
                "user": DB_USER,
                "password": DB_PASSWORD,
                "db": DB_NAME,
                "charset": "utf8mb4",
                "autocommit": True,
                "minsize": 1,
                "maxsize": 10,
                "connect_timeout": DB_CONNECT_TIMEOUT,
            }

            ssl_context = _build_ssl_context()
            if ssl_context is not None:
                pool_kwargs["ssl"] = ssl_context

            self._pool = await aiomysql.create_pool(**pool_kwargs)
            print(f"Database pool initialized: {DB_HOST}:{DB_PORT}/{DB_NAME}")
            if ssl_context is not None:
                print(f"Database SSL enabled (mode={DB_SSL_MODE or 'required'})")

    async def close(self):
        """Close the connection pool."""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
            print("Database pool closed")

    @asynccontextmanager
    async def connection(self):
        """Get a connection from the pool."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")
        pool = self._pool
        async with pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactions with autocommit disabled."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")
        pool = self._pool
        async with pool.acquire() as conn:
            await conn.begin()
            try:
                yield conn
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

    async def execute(self, query: str, params: tuple = ()) -> int:
        """Execute a query and return affected rows."""
        async with self.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return cur.rowcount

    async def fetch_one(self, query: str, params: tuple = ()) -> dict[str, Any] | None:
        """Fetch a single row as a dictionary."""
        async with self.connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def fetch_all(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Fetch all rows as a list of dictionaries."""
        async with self.connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    # ==================== Image Operations ====================

    async def create_image(
        self,
        image_id: str,
        storage_url: str,
        width: int = 0,
        height: int = 0,
        file_size: int = 0,
        hash: str | None = None,
    ) -> str:
        """Create a new image record."""
        query = """
            INSERT INTO images (id, storage_url, width, height, file_size, hash)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        await self.execute(query, (image_id, storage_url, width, height, file_size, hash))
        return image_id

    async def get_image(self, image_id: str) -> dict[str, Any] | None:
        """Get image by ID."""
        return await self.fetch_one("SELECT * FROM images WHERE id = %s", (image_id,))

    async def get_image_with_detections(self, image_id: str) -> dict[str, Any] | None:
        """Get image with all its detections."""
        image = await self.get_image(image_id)
        if not image:
            return None

        detections = await self.fetch_all(
            """SELECT id, label, confidence, bbox_x, bbox_y, bbox_w, bbox_h
               FROM detections WHERE image_id = %s""",
            (image_id,),
        )
        image["detections"] = detections
        return image

    # ==================== Job Operations ====================

    async def create_job(self, image_id: str) -> str:
        """Create a new job for an image."""
        job_id = str(uuid.uuid4())
        query = """
            INSERT INTO jobs (id, image_id, status)
            VALUES (%s, %s, 'pending')
        """
        await self.execute(query, (job_id, image_id))
        return job_id

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Get job by ID."""
        return await self.fetch_one("SELECT * FROM jobs WHERE id = %s", (job_id,))

    async def atomic_pickup_job(self) -> dict[str, Any] | None:
        """
        Atomically pick up a pending job for processing.
        Uses SELECT FOR UPDATE to prevent race conditions.
        Returns the job if one was picked up, None otherwise.
        """
        async with self.transaction() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Lock and select a pending job
                await cur.execute(
                    """SELECT j.*, i.storage_url
                       FROM jobs j
                       JOIN images i ON j.image_id = i.id
                       WHERE j.status = 'pending'
                       ORDER BY j.created_at ASC
                       LIMIT 1
                       FOR UPDATE"""
                )
                job = await cur.fetchone()

                if job:
                    # Update to processing
                    await cur.execute(
                        """UPDATE jobs
                           SET status = 'processing', started_at = NOW()
                           WHERE id = %s""",
                        (job["id"],),
                    )
                    job["status"] = "processing"

                return job

    async def mark_job_done(self, job_id: str):
        """Mark a job as completed."""
        await self.execute("UPDATE jobs SET status = 'done', completed_at = NOW() WHERE id = %s", (job_id,))

    async def mark_job_error(self, job_id: str, error_message: str):
        """Mark a job as failed with error message."""
        await self.execute(
            "UPDATE jobs SET status = 'error', error_message = %s, completed_at = NOW() WHERE id = %s",
            (error_message, job_id),
        )

    # ==================== Detection Operations ====================

    async def create_detection(
        self, image_id: str, label: str, confidence: float, bbox_x: int, bbox_y: int, bbox_w: int, bbox_h: int
    ) -> str:
        """Create a new detection record."""
        detection_id = str(uuid.uuid4())
        query = """
            INSERT INTO detections (id, image_id, label, confidence, bbox_x, bbox_y, bbox_w, bbox_h)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        await self.execute(query, (detection_id, image_id, label, confidence, bbox_x, bbox_y, bbox_w, bbox_h))
        return detection_id

    async def _insert_detection_records(
        self,
        conn: aiomysql.Connection,
        image_id: str,
        detections: list[dict[str, Any]],
    ) -> list[str]:
        if not detections:
            return []

        detection_ids: list[str] = []
        detection_rows: list[tuple[Any, ...]] = []
        polygon_rows: list[tuple[Any, ...]] = []
        embedding_rows: list[tuple[Any, ...]] = []

        for detection in detections:
            detection_id = str(uuid.uuid4())
            detection_ids.append(detection_id)
            detection_rows.append(
                (
                    detection_id,
                    image_id,
                    detection["label"],
                    detection["confidence"],
                    detection["bbox_x"],
                    detection["bbox_y"],
                    detection["bbox_w"],
                    detection["bbox_h"],
                )
            )

            contours = detection.get("contours") or []
            if contours:
                polygon_rows.append(
                    (
                        str(uuid.uuid4()),
                        detection_id,
                        json.dumps(contours),
                        detection.get("simplified", True),
                    )
                )

            embedding = detection.get("embedding")
            if embedding:
                embedding_rows.append(
                    (
                        str(uuid.uuid4()),
                        detection_id,
                        embedding["model_name"],
                        json.dumps(embedding["vector"]),
                    )
                )

        async with conn.cursor() as cur:
            await cur.executemany(
                """
                INSERT INTO detections (id, image_id, label, confidence, bbox_x, bbox_y, bbox_w, bbox_h)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                detection_rows,
            )

            if polygon_rows:
                await cur.executemany(
                    """
                    INSERT INTO polygons (id, detection_id, points_json, simplified)
                    VALUES (%s, %s, %s, %s)
                    """,
                    polygon_rows,
                )

            if embedding_rows:
                await cur.executemany(
                    """
                    INSERT INTO embeddings (id, detection_id, model_name, `vector`)
                    VALUES (%s, %s, %s, %s)
                    """,
                    embedding_rows,
                )

        return detection_ids

    async def create_image_with_detections(
        self,
        image_id: str,
        storage_url: str,
        width: int = 0,
        height: int = 0,
        file_size: int = 0,
        hash: str | None = None,
        detections: list[dict[str, Any]] | None = None,
    ) -> str:
        """Create an image and persist all detections in a single transaction."""
        async with self.transaction() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO images (id, storage_url, width, height, file_size, hash)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (image_id, storage_url, width, height, file_size, hash),
                )

            await self._insert_detection_records(conn, image_id, detections or [])

        return image_id

    async def create_detections_batch(self, image_id: str, detections: list[dict[str, Any]]) -> list[str]:
        """Persist multiple detections, polygons, and embeddings in one transaction."""
        async with self.transaction() as conn:
            return await self._insert_detection_records(conn, image_id, detections)

    async def get_detection(self, detection_id: str) -> dict[str, Any] | None:
        """Get detection by ID with polygon and embedding."""
        detection = await self.fetch_one("SELECT * FROM detections WHERE id = %s", (detection_id,))
        if not detection:
            return None

        # Get polygon
        polygon = await self.fetch_one(
            "SELECT points_json, simplified FROM polygons WHERE detection_id = %s", (detection_id,)
        )
        detection["polygon"] = polygon

        # Get embedding
        embedding = await self.fetch_one(
            "SELECT model_name, `vector` FROM embeddings WHERE detection_id = %s", (detection_id,)
        )
        detection["embedding"] = embedding

        return detection

    # ==================== Polygon Operations ====================

    async def create_polygon(self, detection_id: str, points_json: str, simplified: bool = False) -> str:
        """Create a polygon for a detection."""
        polygon_id = str(uuid.uuid4())
        query = """
            INSERT INTO polygons (id, detection_id, points_json, simplified)
            VALUES (%s, %s, %s, %s)
        """
        await self.execute(query, (polygon_id, detection_id, points_json, simplified))
        return polygon_id

    # ==================== Embedding Operations ====================

    async def create_embedding(self, detection_id: str, model_name: str, vector: str) -> str:
        """Create an embedding for a detection."""
        embedding_id = str(uuid.uuid4())
        query = """
            INSERT INTO embeddings (id, detection_id, model_name, `vector`)
            VALUES (%s, %s, %s, %s)
        """
        await self.execute(query, (embedding_id, detection_id, model_name, vector))
        return embedding_id


# Global database instance getter
_db_service: DatabaseService | None = None


async def get_database() -> DatabaseService:
    """Get the database service singleton."""
    global _db_service
    if _db_service is None:
        _db_service = await DatabaseService.get_instance()
    return _db_service


async def close_database():
    """Close the database connection pool."""
    global _db_service
    if _db_service:
        await _db_service.close()
        _db_service = None
