#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 vX.Y.Z"
  exit 1
fi

TAG="$1"

if [[ ! $TAG =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Tag must be semantic version in the form vMAJOR.MINOR.PATCH"
  exit 2
fi

# Create an annotated tag and push it
git tag -a "$TAG" -m "Release $TAG"
git push origin "$TAG"

echo "Pushed tag $TAG — CI will build and publish the Docker images and create a GitHub Release."