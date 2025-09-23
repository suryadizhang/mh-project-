# =============================================================================
# MyHibachi AI Backend - Lightweight Production Dockerfile
# =============================================================================
# Optimized container for AI/OpenAI service with minimal dependencies

FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash aiuser
USER aiuser
WORKDIR /home/aiuser/app

# Copy and install Python dependencies
COPY --chown=aiuser:aiuser requirements.txt* ./
RUN pip install --user --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    openai==1.3.5 \
    python-multipart==0.0.6 \
    pydantic==2.5.0

# Copy application code
COPY --chown=aiuser:aiuser *.py ./

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Command to run the AI service
CMD ["python", "-m", "uvicorn", "simple_backend_corrected:app", "--host", "0.0.0.0", "--port", "8002"]