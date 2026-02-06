# =============================================================================
# Multi-Stage Dockerfile for MyHibachi Monorepo
# =============================================================================
# Build different components based on ARG COMPONENT
# Usage: docker build --build-arg COMPONENT=admin .
#        docker build --build-arg COMPONENT=customer .
#        docker build --build-arg COMPONENT=api .
#        docker build --build-arg COMPONENT=ai-api .

ARG COMPONENT=customer
ARG NODE_VERSION=20.11.1
ARG PYTHON_VERSION=3.12.7

# =============================================================================
# Base Node.js Image (for frontend components)
# =============================================================================
FROM node:${NODE_VERSION}-alpine@sha256:6e80991f69cc7722c561e5d14d5e72ab47c0d6b6cfb3ae50fb9cf9a7b30fdf97 AS node-base
WORKDIR /app
RUN apk add --no-cache libc6-compat git

# Copy package files
COPY package*.json ./
COPY apps/*/package*.json ./apps/
COPY packages/*/package*.json ./packages/

# Install dependencies
RUN npm ci --only=production --ignore-scripts

# =============================================================================
# Base Python Image (for backend components)
# =============================================================================
FROM python:${PYTHON_VERSION}-alpine@sha256:e75de178bc15e72f3f16bf75a6b484e33d39a456f03fc771a2b3abb9146b75f8 AS python-base
WORKDIR /app

# Install system dependencies (gcc + g++ needed for scikit-learn, numpy compilation)
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libpq-dev \
    linux-headers \
    curl \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# =============================================================================
# Admin Frontend Build Stage
# =============================================================================
FROM node-base AS admin-builder
COPY . .
RUN cd apps/admin && npm run build

# =============================================================================
# Customer Frontend Build Stage
# =============================================================================
FROM node-base AS customer-builder
COPY . .
RUN cd apps/customer && npm run build

# =============================================================================
# Unified Backend Build Stage
# =============================================================================
FROM python-base AS backend-builder

# Install Python dependencies first (for better caching)
COPY apps/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# CACHE_BUST: Invalidate cache for code changes
# Usage: docker compose build --build-arg CACHE_BUST=$(date +%s) staging-api
ARG CACHE_BUST=1
RUN echo "Cache bust: ${CACHE_BUST}"

# Copy backend source code
COPY apps/backend/ .
RUN chown -R appuser:appgroup /app

# =============================================================================
# Final Component Selection Stage
# =============================================================================
FROM scratch AS component-selector

# Admin Frontend Runtime
FROM node:${NODE_VERSION}-alpine@sha256:6e80991f69cc7722c561e5d14d5e72ab47c0d6b6cfb3ae50fb9cf9a7b30fdf97 AS admin
WORKDIR /app
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001 -G appgroup
COPY --from=admin-builder --chown=appuser:appgroup /app/apps/admin/.next/standalone ./
COPY --from=admin-builder --chown=appuser:appgroup /app/apps/admin/.next/static ./.next/static
COPY --from=admin-builder --chown=appuser:appgroup /app/apps/admin/public ./public
USER appuser
EXPOSE 3000
ENV NODE_ENV=production
ENV PORT=3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/healthz || exit 1
CMD ["node", "server.js"]

# Customer Frontend Runtime
FROM node:${NODE_VERSION}-alpine@sha256:6e80991f69cc7722c561e5d14d5e72ab47c0d6b6cfb3ae50fb9cf9a7b30fdf97 AS customer
WORKDIR /app
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001 -G appgroup
COPY --from=customer-builder --chown=appuser:appgroup /app/apps/customer/.next/standalone ./
COPY --from=customer-builder --chown=appuser:appgroup /app/apps/customer/.next/static ./.next/static
COPY --from=customer-builder --chown=appuser:appgroup /app/apps/customer/public ./public
USER appuser
EXPOSE 3000
ENV NODE_ENV=production
ENV PORT=3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/healthz || exit 1
CMD ["node", "server.js"]

# Unified Backend Runtime
FROM python:${PYTHON_VERSION}-alpine@sha256:e75de178bc15e72f3f16bf75a6b484e33d39a456f03fc771a2b3abb9146b75f8 AS backend
WORKDIR /app

# Install runtime dependencies (libpq for psycopg2, curl for healthcheck)
RUN apk add --no-cache curl libpq && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001 -G appgroup

# CRITICAL: Copy Python packages from builder (site-packages contains all installed packages)
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY --from=backend-builder --chown=appuser:appgroup /app ./

USER appuser
EXPOSE 8000
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Final Stage - Select Component Based on Build Arg
# =============================================================================
FROM ${COMPONENT} AS final
