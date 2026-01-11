#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 vX.Y.Z"
  exit 1
fi

TAG="$1"
VERSION="${TAG#v}"  # Remove 'v' prefix for version numbers

if [[ ! $TAG =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Tag must be semantic version in the form vMAJOR.MINOR.PATCH"
  exit 2
fi

echo "Updating version to $VERSION..."

# Update backend/pyproject.toml
UV_LOCK_UPDATED=0
if [ -f "backend/pyproject.toml" ]; then
  # Use a more portable sed approach with explicit backup extension
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '.bak' "s/^version = \".*\"/version = \"$VERSION\"/" backend/pyproject.toml
  else
    # Linux
    sed -i.bak "s/^version = \".*\"/version = \"$VERSION\"/" backend/pyproject.toml
  fi
  rm -f backend/pyproject.toml.bak
  echo "Updated backend/pyproject.toml"
  
  # Update uv.lock to reflect the new version
  if command -v uv &> /dev/null; then
    echo "Updating backend/uv.lock..."
    cd backend && uv lock && cd ..
    echo "Updated backend/uv.lock"
    UV_LOCK_UPDATED=1
  else
    echo "Warning: uv not found, skipping uv.lock update"
  fi
else
  echo "Warning: backend/pyproject.toml not found"
fi

# Update frontend/package.json
if [ -f "frontend/package.json" ]; then
  # Use a more portable sed approach with explicit backup extension
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '.bak' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" frontend/package.json
  else
    # Linux
    sed -i.bak "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" frontend/package.json
  fi
  rm -f frontend/package.json.bak
  echo "Updated frontend/package.json"
else
  echo "Warning: frontend/package.json not found"
fi

# Stage version changes
if [ "$UV_LOCK_UPDATED" -eq 1 ]; then
  git add backend/pyproject.toml backend/uv.lock frontend/package.json
else
  git add backend/pyproject.toml frontend/package.json
fi

# Commit the version changes
git commit -m "Bump version to $VERSION"

# Create an annotated tag
git tag -a "$TAG" -m "Release $TAG"

# Push both commit and tag together to avoid inconsistent state
git push origin main "$TAG"

echo "Pushed tag $TAG — CI will build and publish the Docker images and create a GitHub Release."