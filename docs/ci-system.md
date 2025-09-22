# Change-Aware CI/CD System

## Overview

This advanced CI/CD system implements intelligent change detection for
a monorepo structure, ensuring efficient builds and deployments by
only processing components that have actually changed.

## System Architecture

### Component Mapping

- `myhibachi-frontend` → `admin` + `customer` (Next.js frontends)
- `myhibachi-backend` → `api` (FastAPI backend)
- `myhibachi-ai-backend` → `ai-api` (AI-powered FastAPI backend)

### Key Features

- **Smart Change Detection**: Uses `dorny/paths-filter@v3` for
  accurate file change detection
- **Dynamic Matrix Builds**: Only builds components that have changes
- **Parallel Processing**: Independent component builds and tests
- **Security Integration**: Automated security scanning and compliance
  checks
- **Health-Check Deployments**: Automatic service validation and
  rollback capability
- **Component Isolation**: Each component deployed independently with
  proper service management

## Workflow Files

### 1. `.github/workflows/_filters.yml`

Central path filtering system that detects changes across all
components:

- Monitors component-specific paths
- Detects shared dependency changes
- Outputs change flags for downstream workflows

### 2. `.github/workflows/_reusable-component.yml`

Parameterized build template for all component types:

- Node.js and Python environment setup
- Component-specific build and test logic
- Docker image creation with GitHub Container Registry
- Security scanning and compliance validation

### 3. `.github/workflows/ci-change-aware.yml`

Main CI workflow with dynamic matrix generation:

- Integrates change detection from filters
- Creates dynamic build matrix based on detected changes
- Parallel execution of component builds
- Integration testing between components
- Security gates and compliance verification

### 4. `.github/workflows/deploy-change-aware.yml`

Production deployment with change awareness:

- Environment-specific deployment logic
- Health check validation
- Automatic rollback on failure
- Component-specific service management
- SSH-based VPS deployment

## Deployment Scripts

### `scripts/ci/extract.sh`

Docker container extraction script:

- Pulls built Docker images from registry
- Extracts application files from containers
- Creates deployment packages with proper structure
- Handles both frontend (Next.js standalone) and backend (Python)
  applications

### `scripts/ci/deploy.sh`

VPS deployment automation:

- SSH-based secure deployment
- Atomic deployment switching (zero-downtime)
- Systemd service management
- Component-specific configuration
- Health validation and rollback capability

## Local Development

### Prerequisites

- Docker and Docker Compose
- [act](https://github.com/nektos/act) for local GitHub Actions
  testing
- Node.js 18+ and Python 3.11+

### Setup

1. Copy `.secrets.example` to `.secrets` and configure
2. Install act: `choco install act-cli` (Windows)
3. Start local stack: `docker-compose -f docker-compose.local.yml up`

### Testing Changes

```bash
# Test change detection
act workflow_dispatch -W .github/workflows/_filters.yml

# Test full CI pipeline
act push

# Test specific component build
act workflow_dispatch -W .github/workflows/_reusable-component.yml \
  --input component=admin \
  --input component-type=frontend
```

## Component Types

### Frontend Components (admin, customer)

- **Technology**: Next.js with standalone build mode
- **Build Process**: TypeScript compilation, static optimization,
  standalone server creation
- **Deployment**: Node.js systemd service on port 3000/3001
- **Health Checks**: `/api/health` endpoint validation

### Backend Components (api, ai-api)

- **Technology**: FastAPI with Python 3.11
- **Build Process**: Dependency installation, Python packaging,
  virtual environment setup
- **Deployment**: uvicorn systemd service on port 8001/8002
- **Health Checks**: `/health` endpoint validation

## Security Features

- **Automated Security Scanning**: Integrated Trivy container scanning
- **Secrets Management**: Secure handling of deployment credentials
- **Payment Processing Separation**: AI handles payment info, external
  services process transactions
- **SSH Key Security**: Automated key rotation and secure deployment
  access
- **Service Isolation**: Component-level security boundaries

## Monitoring and Observability

- **Deployment Logging**: Comprehensive deployment process logging
- **Service Health Monitoring**: Systemd status and health endpoint
  validation
- **Error Handling**: Automatic rollback on deployment failures
- **Performance Tracking**: Build time and deployment duration metrics

## Scalability Considerations

- **Component Independence**: Each component can scale independently
- **Resource Optimization**: Only changed components consume CI/CD
  resources
- **Parallel Processing**: Maximum concurrent build and deployment
  efficiency
- **Cache Management**: Docker layer caching and dependency
  optimization

## Future Enhancements

- **Blue-Green Deployments**: Zero-downtime deployment strategy
- **Canary Releases**: Gradual rollout with traffic splitting
- **Multi-Environment Management**: Staging, QA, and production
  pipeline integration
- **Performance Monitoring**: Automated performance regression
  detection

This system provides enterprise-grade CI/CD capabilities while
maintaining simplicity and efficiency for the MyHibachi application
monorepo structure.
