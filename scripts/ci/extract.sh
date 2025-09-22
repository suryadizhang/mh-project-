#!/bin/bash
set -euo pipefail

# Extract runtime from Docker image for deployment
# Usage: ./extract.sh <component> <image_tag>

COMPONENT="${1:-}"
IMAGE_TAG="${2:-}"
REGISTRY="${REGISTRY:-ghcr.io}"
REPO="${GITHUB_REPOSITORY:-$(git config --get remote.origin.url | sed 's/.*github.com[/:]\(.*\)\.git/\1/')}"

if [[ -z "$COMPONENT" || -z "$IMAGE_TAG" ]]; then
    echo "Usage: $0 <component> <image_tag>"
    echo "Example: $0 admin abc123-admin"
    exit 1
fi

echo "📦 Extracting runtime for component: $COMPONENT"
echo "🏷️  Image tag: $IMAGE_TAG"

# Create extraction directory
EXTRACT_DIR="./dist/$COMPONENT"
mkdir -p "$EXTRACT_DIR"

# Component-specific extraction logic
case "$COMPONENT" in
    "admin"|"customer")
        echo "🎯 Extracting Next.js standalone build..."

        # Extract Next.js standalone build from Docker image
        if command -v docker >/dev/null 2>&1 && [[ "${ACT:-}" != "true" ]]; then
            # Pull the built image
            docker pull "${REGISTRY}/${REPO}:${IMAGE_TAG}"

            # Create a temporary container to extract files
            CONTAINER_ID=$(docker create "${REGISTRY}/${REPO}:${IMAGE_TAG}")

            # Extract the standalone build
            docker cp "$CONTAINER_ID:/app/.next/standalone" "$EXTRACT_DIR/app"
            docker cp "$CONTAINER_ID:/app/.next/static" "$EXTRACT_DIR/app/.next/static"
            docker cp "$CONTAINER_ID:/app/public" "$EXTRACT_DIR/app/public"

            # Copy package.json for dependencies info
            docker cp "$CONTAINER_ID:/app/package.json" "$EXTRACT_DIR/package.json" || true

            # Cleanup
            docker rm "$CONTAINER_ID"

            # Create startup script
            cat > "$EXTRACT_DIR/start.sh" << 'EOF'
#!/bin/bash
cd /srv/COMPONENT_NAME/app
NODE_ENV=production node server.js
EOF
            chmod +x "$EXTRACT_DIR/start.sh"
            sed -i "s/COMPONENT_NAME/$COMPONENT/g" "$EXTRACT_DIR/start.sh"

        else
            echo "⚠️  Running in local mode - creating mock extraction"
            mkdir -p "$EXTRACT_DIR/app"
            echo "Mock $COMPONENT build" > "$EXTRACT_DIR/app/server.js"
        fi

        echo "✅ Next.js standalone build extracted to $EXTRACT_DIR"
        ;;

    "api"|"ai-api")
        echo "🎯 Extracting Python API application..."

        if command -v docker >/dev/null 2>&1 && [[ "${ACT:-}" != "true" ]]; then
            # Pull the built image
            docker pull "${REGISTRY}/${REPO}:${IMAGE_TAG}"

            # Create a temporary container to extract files
            CONTAINER_ID=$(docker create "${REGISTRY}/${REPO}:${IMAGE_TAG}")

            # Extract the Python application
            docker cp "$CONTAINER_ID:/app" "$EXTRACT_DIR/app"
            docker cp "$CONTAINER_ID:/requirements.txt" "$EXTRACT_DIR/requirements.txt" || true

            # Cleanup
            docker rm "$CONTAINER_ID"

            # Create startup script
            cat > "$EXTRACT_DIR/start.sh" << 'EOF'
#!/bin/bash
cd /srv/COMPONENT_NAME/app
python -m uvicorn main:app --host 0.0.0.0 --port 8000
EOF
            chmod +x "$EXTRACT_DIR/start.sh"
            sed -i "s/COMPONENT_NAME/$COMPONENT/g" "$EXTRACT_DIR/start.sh"

        else
            echo "⚠️  Running in local mode - creating mock extraction"
            mkdir -p "$EXTRACT_DIR/app"
            echo "Mock $COMPONENT API" > "$EXTRACT_DIR/app/main.py"
        fi

        echo "✅ Python API application extracted to $EXTRACT_DIR"
        ;;

    *)
        echo "❌ Unknown component: $COMPONENT"
        exit 1
        ;;
esac

# Create deployment manifest
cat > "$EXTRACT_DIR/deploy-manifest.json" << EOF
{
  "component": "$COMPONENT",
  "image_tag": "$IMAGE_TAG",
  "extracted_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "git_sha": "${GITHUB_SHA:-$(git rev-parse HEAD)}",
  "git_ref": "${GITHUB_REF_NAME:-$(git branch --show-current)}",
  "repo": "$REPO"
}
EOF

# Package for deployment
echo "📦 Creating deployment package..."
tar -czf "${COMPONENT}-${IMAGE_TAG}.tar.gz" -C "./dist" "$COMPONENT"

echo "✅ Runtime extraction completed!"
echo "📁 Extracted to: $EXTRACT_DIR"
echo "📦 Package: ${COMPONENT}-${IMAGE_TAG}.tar.gz"
echo "📋 Manifest: $EXTRACT_DIR/deploy-manifest.json"

# List contents for verification
echo ""
echo "📋 Package contents:"
find "$EXTRACT_DIR" -type f -exec ls -lh {} \; | head -20
