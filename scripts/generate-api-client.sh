#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Generating OpenAPI TypeScript client...${NC}"

# Ensure API server is running
API_URL="${API_URL:-http://localhost:8000}"
echo -e "${YELLOW}📡 Checking API server at ${API_URL}...${NC}"

# Function to check if API is running
check_api() {
    if curl -s "${API_URL}/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Start API if not running
if ! check_api; then
    echo -e "${YELLOW}🚀 Starting API server...${NC}"
    cd "$(dirname "$0")/../apps/api"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    API_PID=$!

    # Wait for API to be ready
    for i in {1..30}; do
        echo -e "${YELLOW}⏳ Waiting for API to start (${i}/30)...${NC}"
        if check_api; then
            echo -e "${GREEN}✅ API server is ready!${NC}"
            break
        fi
        sleep 2
    done

    if ! check_api; then
        echo -e "${RED}❌ API server failed to start${NC}"
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
else
    echo -e "${GREEN}✅ API server is already running${NC}"
    API_PID=""
fi

# Generate OpenAPI schema
echo -e "${BLUE}📥 Fetching OpenAPI schema...${NC}"
SCHEMA_FILE="$(dirname "$0")/../packages/api-client/openapi.json"
mkdir -p "$(dirname "$SCHEMA_FILE")"

if curl -s "${API_URL}/openapi.json" -o "$SCHEMA_FILE"; then
    echo -e "${GREEN}✅ OpenAPI schema saved to ${SCHEMA_FILE}${NC}"
else
    echo -e "${RED}❌ Failed to fetch OpenAPI schema${NC}"
    [[ -n "$API_PID" ]] && kill $API_PID 2>/dev/null || true
    exit 1
fi

# Generate TypeScript types
echo -e "${BLUE}🔧 Generating TypeScript types...${NC}"
cd "$(dirname "$0")/../packages/api-client"

if npm run generate; then
    echo -e "${GREEN}✅ TypeScript types generated successfully${NC}"
else
    echo -e "${RED}❌ Failed to generate TypeScript types${NC}"
    [[ -n "$API_PID" ]] && kill $API_PID 2>/dev/null || true
    exit 1
fi

# Cleanup
if [[ -n "$API_PID" ]]; then
    echo -e "${YELLOW}🧹 Stopping API server...${NC}"
    kill $API_PID 2>/dev/null || true
fi

echo -e "${GREEN}🎉 OpenAPI client generation complete!${NC}"
echo -e "${BLUE}📋 Generated files:${NC}"
echo -e "   - ${SCHEMA_FILE}"
echo -e "   - packages/api-client/src/types/api.ts"
