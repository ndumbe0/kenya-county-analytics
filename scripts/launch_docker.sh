#!/bin/bash
# Kenya County Analytics - Docker Launch Script
echo "=========================================="
echo "Kenya County Analytics Platform (Docker)"
echo "=========================================="

cd "$(dirname "$0")/.."

# Build and start containers
docker-compose up --build -d

echo "=========================================="
echo "API:        http://localhost:8000"
echo "Dashboard:  http://localhost:8000/dashboard"
echo "API Docs:   http://localhost:8000/docs"
echo "=========================================="
docker-compose logs -f api