# Local CI/CD Development Guide

This guide shows how to test the change-aware CI/CD system locally
before deploying to production.

## Prerequisites

- Docker and Docker Compose
- [act](https://github.com/nektos/act) - Run GitHub Actions locally
- Node.js 18+ and Python 3.11+
- SSH key pair for deployment testing

## Setup

1. **Install act (GitHub Actions runner)**:

   ```bash
   # Windows (using Chocolatey)
   choco install act-cli

   # Or download from https://github.com/nektos/act/releases
   ```

2. **Configure secrets**:

   ```bash
   # Copy and fill in your secrets
   cp .secrets.example .secrets

   # Edit .secrets with your actual values
   # Note: Use test/staging values, not production
   ```

3. **Create act configuration**:
   ```bash
   # .actrc (act configuration file)
   echo "--secret-file .secrets" > .actrc
   echo "--platform ubuntu-latest=catthehacker/ubuntu:act-latest" >> .actrc
   ```

## Local Testing

### Test Change Detection

Simulate file changes and test the path filter system:

```bash
# Test change detection for specific components
act workflow_dispatch -W .github/workflows/_filters.yml --input component=admin

# View detected changes
act workflow_dispatch -W .github/workflows/ci-change-aware.yml --dry-run
```

### Test Component Builds

Test individual component builds locally:

```bash
# Test admin frontend build
act workflow_dispatch -W .github/workflows/_reusable-component.yml \
  --input component=admin \
  --input component-type=frontend \
  --input source-path=myhibachi-frontend

# Test API backend build
act workflow_dispatch -W .github/workflows/_reusable-component.yml \
  --input component=api \
  --input component-type=backend \
  --input source-path=myhibachi-backend-fastapi
```

### Test Full CI Pipeline

Test the complete CI pipeline with change detection:

```bash
# Simulate a push event (tests change detection)
act push

# Test specific branch
act push -b feature/new-component

# Test pull request
act pull_request
```

### Test Deployment Pipeline

**⚠️ Warning**: Only test deployment against staging/test servers,
never production!

```bash
# Test deployment workflow (use staging secrets!)
act workflow_dispatch -W .github/workflows/deploy-change-aware.yml \
  --input environment=staging \
  --input components='["admin"]'

# Test manual deployment
act workflow_dispatch -W .github/workflows/deploy-change-aware.yml \
  --input deploy-all=true
```

## Local Development Workflow

### 1. Component Development

```bash
# Start development server for frontend components
cd myhibachi-frontend
npm run dev

# Or for backend components
cd myhibachi-backend
python -m uvicorn main:app --reload --port 8001
```

### 2. Test Changes Locally

```bash
# Make your changes, then test CI locally
act push --dry-run  # See what would run

# Run actual tests
act push
```

### 3. Deployment Testing

```bash
# Test deployment package creation
./scripts/ci/extract.sh admin latest

# Test deployment to staging (requires staging server)
SSH_HOST=staging.yourdomain.com ./scripts/ci/deploy.sh admin
```

## Docker Local Development

Use Docker Compose for full stack development:

```bash
# Start all services
docker-compose -f docker-compose.local.yml up

# Start specific services
docker-compose -f docker-compose.local.yml up admin api

# View logs
docker-compose -f docker-compose.local.yml logs -f admin
```

## Debugging Tips

### 1. Act Debugging

```bash
# Verbose output
act push -v

# Step through workflow
act push --dry-run

# Use specific runner image
act push --platform ubuntu-latest=catthehacker/ubuntu:act-20.04
```

### 2. Change Detection Debugging

```bash
# Check what files changed
git diff --name-only HEAD~1 HEAD

# Test path filters manually
echo "myhibachi-frontend/src/components/Header.tsx" | grep -E "myhibachi-frontend/"
```

### 3. Component Build Debugging

```bash
# Test individual component builds
cd myhibachi-frontend
npm run build
npm run lint
npm run test

# Test Docker builds
docker build -f docker/frontend.Dockerfile -t test-admin .
```

### 4. Deployment Debugging

```bash
# Test SSH connection
ssh -i ~/.ssh/deploy_key deployer@staging.yourdomain.com

# Test deployment scripts locally
./scripts/ci/extract.sh admin latest
tar -tzf admin-latest.tar.gz  # View package contents
```

## Common Issues

### Act Issues

- **Permission denied**: Ensure Docker is running and you have
  permissions
- **Secret not found**: Check `.secrets` file and `.actrc`
  configuration
- **Workflow not found**: Use correct workflow path with `-W` flag

### Docker Issues

- **Build failures**: Check Dockerfiles and build contexts
- **Port conflicts**: Ensure ports aren't already in use
- **Volume mounts**: Verify paths exist and have correct permissions

### SSH/Deployment Issues

- **SSH key format**: Ensure private key is in OpenSSH format
- **Host verification**: Add `-o StrictHostKeyChecking=no` for testing
- **Service startup**: Check systemd logs with
  `journalctl -u service-name`

## Production Deployment

Once local testing passes:

1. **Push to GitHub**: Changes trigger real CI/CD pipeline
2. **Monitor Actions**: Check GitHub Actions tab for pipeline status
3. **Verify Deployment**: Check production services and health
   endpoints
4. **Rollback if needed**: Use deployment workflow to rollback

## Security Notes

- Never commit `.secrets` file
- Use staging/test credentials for local testing
- Rotate deployment keys regularly
- Monitor deployment logs for sensitive data leaks

## Performance Tips

- Use `--dry-run` flag for quick testing
- Cache Docker layers with multi-stage builds
- Use specific component testing instead of full pipeline
- Keep deployment packages small with `.dockerignore`

This local development setup ensures you can test the entire CI/CD
pipeline safely before deploying to production.
