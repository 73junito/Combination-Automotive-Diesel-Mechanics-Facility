#!/usr/bin/env bash
set -euo pipefail

# Wrapper to run the cad-converter Docker image for converting CAD files.
# Usage: scripts/docker_export.sh --src Drawings/CAD/Project/FILE.dwg [--add-git]

IMAGE_NAME=cad-converter

PWD_DIR=$(pwd)

docker run --rm -v "$PWD_DIR":/workspace "$IMAGE_NAME" "$@"
