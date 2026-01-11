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
if [ -f "backend/pyproject.toml" ]; then
  sed -i.bak "s/^version = \".*\"/version = \"$VERSION\"/" backend/pyproject.toml
  rm backend/pyproject.toml.bak
  echo "Updated backend/pyproject.toml"
else
  echo "Warning: backend/pyproject.toml not found"
fi

# Update frontend/package.json
if [ -f "frontend/package.json" ]; then
  sed -i.bak "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" frontend/package.json
  rm frontend/package.json.bak
  echo "Updated frontend/package.json"
else
  echo "Warning: frontend/package.json not found"
fi

# Commit the version changes
git add backend/pyproject.toml frontend/package.json
git commit -m "Bump version to $VERSION"

# Create an annotated tag and push it
git tag -a "$TAG" -m "Release $TAG"
git push origin main
git push origin "$TAG"

echo "Pushed tag $TAG — CI will build and publish the Docker images and create a GitHub Release."