# ==============================================================================
# The Forwarded Seal — Production Backend Container
# Multi-stage security-hardened Dockerfile for FastAPI, OpenCV, and Cryptography
# ==============================================================================

FROM python:3.10-slim AS builder

WORKDIR /app

# Install system dependencies required for building C extensions and OpenCV headless
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    gcc \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ==============================================================================
# Final Production Runtime Stage
# ==============================================================================
FROM python:3.10-slim AS runner

WORKDIR /app

# Install runtime libraries for OpenCV, PostgreSQL client, and healthcheck
RUN apt-get update && apt-get install --no-install-recommends -y \
    libpq5 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root application user for defense-in-depth container isolation
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

# Create directories for persistent uploads, published notices, and keys
RUN mkdir -p /app/uploads /app/published /app/keys && \
    chown -R appuser:appgroup /app

# Copy application source code
COPY --chown=appuser:appgroup . /app

# Switch to non-root execution
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Start production ASGI server with multiple workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]

