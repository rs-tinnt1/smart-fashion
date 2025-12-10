# ===========================================
# Dockerfile - Production Optimized (Poetry)
# Multi-stage build for minimal image size
# ===========================================

# Stage 1: Dependencies builder
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=2.1.3

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR /build

# Copy only dependency files first (for better layer caching)
COPY pyproject.toml poetry.lock ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv

# Install dependencies using poetry directly (simpler than export in Poetry 2.x)
RUN . /opt/venv/bin/activate && \
    poetry install --only main --no-root && \
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete 2>/dev/null || true

# ===========================================
# Stage 2: Production runtime
# ===========================================
FROM python:3.12-slim AS runtime

# Install only runtime dependencies (OpenCV requirements)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code (order by change frequency for better caching)
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser templates/ ./templates/
COPY --chown=appuser:appuser static/ ./static/
COPY --chown=appuser:appuser main.py worker.py ./

# Create required directories
RUN mkdir -p /app/models /app/outputs /app/uploads && \
    chown -R appuser:appuser /app

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=2 \
    PYTHONFAULTHANDLER=1 \
    # Uvicorn settings
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    UVICORN_WORKERS=1 \
    # Performance tuning
    OMP_NUM_THREADS=4

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${UVICORN_PORT}')" || exit 1

# Production command - use full path to ensure venv is used
CMD ["/opt/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
