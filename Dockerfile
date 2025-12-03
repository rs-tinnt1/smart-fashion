# Stage 1: Builder - cài đặt dependencies
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy và cài đặt Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - chỉ giữ lại những gì cần thiết
FROM python:3.12-slim AS runtime

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy Python packages từ builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy source code (sử dụng .dockerignore để loại bỏ files không cần thiết)
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser templates/ ./templates/
COPY --chown=appuser:appuser static/ ./static/

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    PATH=/home/appuser/.local/bin:$PATH \
    MONGO_URI="" \
    MONGO_DB="" \
    MINIO_ENDPOINT="" \
    MINIO_ROOT_USER="" \
    MINIO_ROOT_PASSWORD="" \
    MINIO_BUCKET="" \
    MINIO_REGION="" \
    MINIO_SECURE=""

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${UVICORN_PORT}')" || exit 1

# Start server
CMD ["sh", "-c", "uvicorn main:app --host ${UVICORN_HOST} --port ${UVICORN_PORT}"]
