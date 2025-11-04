#!/bin/sh
set -e

# Bind address (port); default 0.0.0.0:80
BIND_ADDR="${BIND_ADDR:-0.0.0.0:80}"
USE_SSL="${USE_SSL:-false}"
CERT_FILE="${CERT_FILE:-/app/certs/cert.pem}"
KEY_FILE="${KEY_FILE:-/app/certs/key.pem}"

if [ "$USE_SSL" = "true" ]; then
  # Ensure certs exist; if not, generate a quick self-signed pair for localhost
  if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "[start] No cert/key found. Generating self-signed certificate for localhost..."
    mkdir -p "$(dirname "$CERT_FILE")"
    # openssl should be preinstalled in image; this is a safety check
    if ! command -v openssl >/dev/null 2>&1; then
      echo "[start] openssl not found in image. Attempting install..."
      apt-get update && apt-get install -y --no-install-recommends openssl && rm -rf /var/lib/apt/lists/*
    fi
    openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
      -subj "/CN=localhost" \
      -keyout "$KEY_FILE" -out "$CERT_FILE"
  fi
  echo "[start] Launching Gunicorn with TLS on $BIND_ADDR"
  exec gunicorn epos.wsgi:application --bind "$BIND_ADDR" --certfile "$CERT_FILE" --keyfile "$KEY_FILE"
else
  echo "[start] Launching Gunicorn (HTTP) on $BIND_ADDR"
  exec gunicorn epos.wsgi:application --bind "$BIND_ADDR"
fi
