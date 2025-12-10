#!/bin/sh
set -eu

# Cross-platform pre-check for Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker CLI not found. Please install Docker Desktop (macOS/Windows) or Docker Engine (Linux) and retry."
    exit 1
fi
echo "Docker present: $(docker --version)"

# Paths: expect this script to be run from within the extracted bundle directory,
# where docker_build_files contains the image tar and env file.
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
BUNDLE_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
FILES_DIR="$BUNDLE_DIR/docker_build_files"

IMAGE_TAR="$FILES_DIR/epos_docker.tar"
ENV_FILE="$FILES_DIR/env"

if [ ! -f "$IMAGE_TAR" ]; then
    echo "Image tar not found at $IMAGE_TAR. Ensure you extracted the build zip correctly."
    exit 1
fi

# Load configuration from .env if present (EPOS_* vars)
if [ -f "$ENV_FILE" ]; then
    echo "Loading configuration from $ENV_FILE"
    # Export variables defined in the env file
    set -a
    . "$ENV_FILE" || true
    set +a
fi
# print contents of env file for debugging
# else echo "$ENV_FILE not found; proceeding with defaults."
if [ -f "$ENV_FILE" ]; then
    echo "Contents of $ENV_FILE:"
    cat "$ENV_FILE"
else
    echo "$ENV_FILE not found; proceeding with defaults."
fi



# Determine mapped port, container name, image tag (with defaults)
PORT=${EPOS_PORT:-"8090"}
NAME=${EPOS_CONTAINER_NAME:-"epos-web"}
IMAGE_TAG=${EPOS_IMAGE_TAG:-"epos-web:latest"}

# If a container with same name exists, stop and remove to ensure fresh run
if docker ps -a --format '{{.Names}}' | grep -q "^${NAME}$"; then
    echo "Container ${NAME} exists. Stopping and removing..."
    docker stop "$NAME" >/dev/null 2>&1 || true
    docker rm "$NAME" >/dev/null 2>&1 || true
fi

# Remove existing image tag to avoid using stale layers when running
if docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
    echo "Removing existing image $IMAGE_TAG..."
    docker rmi -f "$IMAGE_TAG" >/dev/null 2>&1 || true
fi

echo "Loading Docker image from $(basename "$IMAGE_TAR")..."
docker load -i "$IMAGE_TAR"

# Detect image platform to avoid host/arch mismatch, allow override via EPOS_PLATFORM
IMG_PLATFORM_OVERRIDE=${EPOS_PLATFORM:-""}
if [ -n "$IMG_PLATFORM_OVERRIDE" ]; then
    echo "Using platform override from env: $IMG_PLATFORM_OVERRIDE"
    IMG_PLATFORM="$IMG_PLATFORM_OVERRIDE"
else
    IMG_PLATFORM=$(docker image inspect "$IMAGE_TAG" --format '{{.Os}}/{{.Architecture}}' 2>/dev/null || true)
fi
PLATFORM_ARG=""
if [ -n "$IMG_PLATFORM" ]; then
    echo "Detected image platform: $IMG_PLATFORM"
    PLATFORM_ARG="--platform $IMG_PLATFORM"
fi

echo "Running Docker container ${NAME} from ${IMAGE_TAG}..."
RUN_ARGS="-d -p \"$PORT:$PORT\" --restart unless-stopped --name \"$NAME\" $PLATFORM_ARG"
if [ -f "$ENV_FILE" ]; then
    # Pass env vars and also mount the file to the expected path inside the app
    # Many apps read ".env" from project root; mount as /ePOS/.env (read-only)
    docker run -d -p "$PORT:$PORT" --restart unless-stopped --name "$NAME" $PLATFORM_ARG \
        --env-file "$ENV_FILE" \
        -v "$ENV_FILE":/ePOS/.env:ro \
        "$IMAGE_TAG"
else
    docker run -d -p "$PORT:$PORT" --restart unless-stopped --name "$NAME" $PLATFORM_ARG "$IMAGE_TAG"
fi
echo "Docker container '${NAME}' is running and accessible on port ${PORT}."

# Verify container is running; if not, show logs and exit with error
if ! docker ps --format '{{.Names}}' | grep -q "^${NAME}$"; then
    echo "Container ${NAME} is not running. Showing logs:"
    docker logs "$NAME" || true
    exit 1
fi

echo "Access the application at http://localhost:${PORT}"
