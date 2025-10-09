# =============================================================================
# MyHibachi Backend - Multi-Stage Production Dockerfile
# =============================================================================
# This Dockerfile creates a secure, optimized production image for the FastAPI backend
# Features: Multi-stage build, non-root user, minimal attack surface, health checks

# =============================================================================
# Stage 1: Build Dependencies (Python Builder)
# =============================================================================
FROM python:3.11-slim as builder

# Set build-time environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and switch to app user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /home/appuser

# Create virtual environment
RUN python -m venv /home/appuser/venv
ENV PATH="/home/appuser/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# =============================================================================
# Stage 2: Production Runtime
# =============================================================================
FROM python:3.11-slim as production

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/venv/bin:$PATH" \
    ENVIRONMENT=production \
    PYTHONPATH=/home/appuser/app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user (non-root for security)
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /home/appuser/app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /home/appuser/venv /home/appuser/venv

# Copy application code
COPY --chown=appuser:appuser ./app ./app

# Create necessary directories with proper permissions
RUN mkdir -p /home/appuser/app/logs \
    /home/appuser/app/data \
    /home/appuser/app/weekly_databases \
    /tmp/prometheus_multiproc_dir \
    && chmod 755 /home/appuser/app/logs \
    && chmod 755 /home/appuser/app/data \
    && chmod 755 /home/appuser/app/weekly_databases

# Expose ports (8000 for API, 8001 for metrics)
EXPOSE 8000 8001

# Enhanced health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Default production command with optimized settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]

# =============================================================================
# Stage 3: Development (Optional)
# =============================================================================
FROM production as development

# Switch back to root for development tools installation
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    vim \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Switch back to app user
USER appuser

# Install development Python packages
RUN pip install debugpy pytest-watch ipython

# Set development environment
ENV ENVIRONMENT=development \
    DEBUG=true

# Override for development with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]