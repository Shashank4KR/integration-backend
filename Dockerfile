# syntax=docker/dockerfile:1

# -------------------------------------------------------------
# Stage 1: Build stage
# -------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------------
# Stage 2: Production runtime stage
# -------------------------------------------------------------
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000 \
    ENVIRONMENT=production

WORKDIR /app

# Install minimal runtime dependencies (curl for healthcheck, libpq5 for PostgreSQL)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and group
RUN groupadd --system --gid 10001 appgroup && \
    useradd --system --uid 10001 --gid appgroup --no-create-home appuser

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Copy application source code and migrations
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup alembic.ini ./

# Switch to unprivileged user
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
