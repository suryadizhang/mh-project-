# GitHub Actions Secrets Configuration Guide

> **Last Updated:** February 2, 2026
> **Purpose:** Required secrets for CI/CD workflows

## Required GitHub Repository Secrets

Go to: **GitHub → Repository → Settings → Secrets and variables → Actions**

### Cloudflare Access (SSH via Zero Trust)

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `CF_ACCESS_CLIENT_ID` | Cloudflare Access Service Token Client ID | Cloudflare Zero Trust → Access → Service Tokens → Create Token |
| `CF_ACCESS_CLIENT_SECRET` | Cloudflare Access Service Token Secret | Same as above (save at creation time) |
| `CF_SSH_HOSTNAME` | SSH hostname via Cloudflare Tunnel | e.g., `ssh.mhapi.mysticdatanode.net` (must match Cloudflare Access app) |

### VPS Configuration

| Secret Name | Description | Value |
|-------------|-------------|-------|
| `VPS_USER` | SSH user on VPS | `root` |
| `VPS_STAGING_PATH` | Staging backend directory | `/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend` |
| `VPS_PRODUCTION_PATH` | Production backend directory | `/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend` |

### Optional: E2E Tests

| Secret Name | Description | Value |
|-------------|-------------|-------|
| `STAGING_API_URL` | Staging API URL for E2E tests | `https://staging-api.mysticdatanode.net` |

## GitHub Environments

For production deployments, configure a **production** environment with approval:

1. Go to **Settings → Environments → New environment**
2. Name: `production`
3. Enable **Required reviewers** (optional but recommended)
4. Add yourself as a required reviewer for production deploys

Optional: Create a **staging** environment without reviewers.

## Verify Secrets Are Configured

Run this checklist:

- [ ] `CF_ACCESS_CLIENT_ID` - Cloudflare Service Token ID
- [ ] `CF_ACCESS_CLIENT_SECRET` - Cloudflare Service Token Secret
- [ ] `CF_SSH_HOSTNAME` - SSH hostname (e.g., `ssh.mhapi.mysticdatanode.net`)
- [ ] `VPS_USER` - SSH user (`root`)
- [ ] `VPS_STAGING_PATH` - Staging path
- [ ] `VPS_PRODUCTION_PATH` - Production path (can be same as staging if using same directory)
- [ ] `STAGING_API_URL` - (optional) Staging API URL for E2E tests

## Testing the Workflows

### Test Staging Deployment

```bash
# Push a change to the dev branch
git checkout dev
echo "# test" >> apps/backend/README.md
git add . && git commit -m "test: trigger staging deploy"
git push origin dev
```

### Test Production Deployment (Manual Trigger)

1. Go to **GitHub → Actions**
2. Select **"Deploy Backend to Production"**
3. Click **"Run workflow"** → Select `main` branch → Click **"Run workflow"**

## Workflow Files

| Workflow | File | Trigger | Environment |
|----------|------|---------|-------------|
| Staging Deploy | `.github/workflows/deploy-backend-staging.yml` | Push to `dev` | staging |
| Production Deploy | `.github/workflows/deploy-backend-production.yml` | Push to `main` or manual | production |
| CI Tests | `.github/workflows/ci-cd.yml` | Push/PR to main/dev | N/A |

## Troubleshooting

### "SSH connection failed"

- Verify Cloudflare Access Service Token is valid
- Check that SSH hostname resolves correctly
- Ensure Cloudflare Tunnel is running on VPS

### "Docker compose command not found"

- SSH into VPS and verify Docker is installed
- Check Docker Compose version: `docker compose version`

### "Health check failed"

- Check container logs: `docker compose -f docker-compose.prod.yml logs -f`
- Verify .env file exists with correct database credentials
- Check PostgreSQL is running: `systemctl status postgresql`
