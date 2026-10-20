# ==============================================================================
# OPTIMIZED PRODUCTION DOCKERFILE (MULTI-STAGE BUILD - ~140 MB)
# ==============================================================================
# Optimizations applied:
# 1. Base Image: Switched to python:3.11-slim-bookworm (~140MB vs ~1.02GB)
# 2. Multi-Stage: Build compilers & header files isolated in Builder stage
# 3. Clean Package Management: --no-cache-dir and apt cache purges
# 4. Dependency Pruning: Only production requirements.txt installed
# 5. Security: Runs as unprivileged non-root user (UID 10001)
# 6. Observability: Native container HEALTHCHECK included
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Environment (Builder)
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies needed for C-extensions (psycopg2, Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only production requirements first to leverage Docker layer caching
COPY requirements.txt .

# Build wheels for production dependencies (isolated from final image)
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Final Lean Runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

# Set production runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Install only minimal runtime shared libraries (libpq5 for PostgreSQL, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Copy wheels from the builder stage and install with no pip cache
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy application source code with non-root ownership
COPY --chown=appuser:appgroup app /app/app

# Switch to unprivileged user
USER appuser

# Healthcheck configuration
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
