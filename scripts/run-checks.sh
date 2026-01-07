#!/bin/bash
# Run all local checks that are part of CI/CD
# This script should be run before committing to ensure everything passes CI

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=================================================="
echo "Running all CI checks locally..."
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

failed_checks=()

# Function to run a check and track results
run_check() {
    local name=$1
    local command=$2
    local working_dir=${3:-.}
    
    echo "${YELLOW}▶ Running: $name${NC}"
    
    if (cd "$PROJECT_ROOT/$working_dir" && eval "$command"); then
        echo "${GREEN}✓ $name passed${NC}"
        echo ""
    else
        echo "${RED}✗ $name failed${NC}"
        echo ""
        failed_checks+=("$name")
    fi
}

# Backend checks
echo "${YELLOW}=== BACKEND CHECKS ===${NC}"
echo ""

run_check "Backend: Ruff linting" "uv run ruff check app/ tests/" "backend"

# Frontend checks
echo "${YELLOW}=== FRONTEND CHECKS ===${NC}"
echo ""

run_check "Frontend: Install dependencies" "npm install" "frontend"
run_check "Frontend: Linting" "npm run lint" "frontend"

# Docker build checks
echo "${YELLOW}=== DOCKER BUILD CHECKS ===${NC}"
echo ""

# Skipping Docker builds for faster local checks - uncomment to test
# run_check "Docker: Build backend image" "docker build -f backend/Dockerfile backend/ -t mealplanner-backend:latest" "."
# run_check "Docker: Build frontend image" "docker build -f frontend/Dockerfile frontend/ -t mealplanner-frontend:latest" "."

# Summary
echo ""
echo "=================================================="
if [ ${#failed_checks[@]} -eq 0 ]; then
    echo "${GREEN}✓ All checks passed!${NC}"
    echo "=================================================="
    exit 0
else
    echo "${RED}✗ The following checks failed:${NC}"
    for check in "${failed_checks[@]}"; do
        echo "  - $check"
    done
    echo "=================================================="
    exit 1
fi
