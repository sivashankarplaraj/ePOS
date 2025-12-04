# ePOS Docker Guide

This document shows how to build, run, save, and load the ePOS Docker image using Docker Compose on Windows PowerShell and Linux/macOS shells. Examples are copy‑paste ready.

## Prerequisites

- Docker Desktop installed and running
- PowerShell (pwsh) shell
- Clone of this repo with the working directory set to the project root

## Environment variables

Configure `.env` in the project root. At minimum, set:

```
SECRET_KEY=replace-with-long-secret
DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1
SHOP_NUMBER=1
```

Compose reads `.env` automatically and passes values to the container.

## Build and run with Docker Compose

Compose file: `compose.yml` (already in the repo).

Windows (PowerShell):

```powershell
# From the project root
docker compose up -d --build

# Check logs
docker compose logs --no-log-prefix web

# Stop
docker compose down
```

Linux/macOS (bash/zsh):

```bash
# From the project root
docker compose up -d --build

# Check logs
docker compose logs --no-log-prefix web | tail -n 100

# Stop
docker compose down
```

The app listens on port 8090:

```
http://localhost:8090
```

## Static files (CSS/JS/images)

Static files are served by WhiteNoise and collected to `production_files`. Compose mounts this folder so assets persist:

- Host: `./production_files`
- Container: `/ePOS/production_files`

Run collectstatic any time assets change:

Windows (PowerShell):

```powershell
docker compose exec web python manage.py collectstatic --noinput
```

Linux/macOS (bash/zsh):

```bash
docker compose exec web python manage.py collectstatic --noinput
```

If you see MIME type errors for CSS/JS or 404s under `/static/`, re‑run `collectstatic` and reload the page.

## Rebuild after code changes

When you change Python code or dependencies, rebuild:

Windows (PowerShell):

```powershell
docker compose up -d --build
```

Linux/macOS (bash/zsh):

```bash
docker compose up -d --build
```

If you changed `requirements.txt`, Compose rebuilds the image and reinstalls dependencies.

## Save and load the image (portable)

To export the built image to a tar file (for offline transfer):

Windows (PowerShell):

```powershell
# List images (look for epos-web:latest)
docker image ls --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}" | findstr epos

# Save the image
docker save -o D:\\epos-docker.tar epos-web:latest
```

Linux/macOS (bash/zsh):

```bash
# List images (look for epos-web:latest)
docker image ls --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}' | grep epos

# Save the image
docker save -o ~/epos-docker.tar epos-web:latest
```

On another machine, load and run:

Windows (PowerShell):

```powershell
docker load -i D:\\epos-docker.tar

# Run directly (without compose)
docker run -d -p 8090:8090 --name epos-web epos-web:latest

# Or use compose if you copied the repo and .env
docker compose up -d
```

Linux/macOS (bash/zsh):

```bash
docker load -i ~/epos-docker.tar

# Run directly (without compose)
docker run -d -p 8090:8090 --name epos-web epos-web:latest

# Or use compose if you copied the repo and .env
docker compose up -d
```

## Common commands

Windows (PowerShell):

```powershell
# Start (build if needed)
docker compose up -d --build

# Stop
docker compose down

# Logs
docker compose logs --no-log-prefix web

# Shell inside container
docker compose exec web sh

# Django management commands
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py collectstatic --noinput
```

Linux/macOS (bash/zsh):

```bash
# Start (build if needed)
docker compose up -d --build

# Stop
docker compose down

# Logs
docker compose logs --no-log-prefix web | tail -n 100

# Shell inside container
docker compose exec web sh

# Django management commands
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py collectstatic --noinput
```

## Troubleshooting

- "Refused to apply style/script… MIME type 'text/html'": run `collectstatic` and ensure requests to `/static/...` return 200.
- 404 for `/static/...`: check the file exists under `staticfiles/...` and is present in `production_files`. If missing, run `collectstatic`.
- Compose warning: `version is obsolete`: safe to ignore; the `services:` section is what matters.
- Port conflict: ensure nothing else is listening on 8090, or change the port mapping in `compose.yml`.

## Notes

- The container runs Gunicorn bound to `0.0.0.0:8090`.
- WhiteNoise serves static assets from `/ePOS/production_files` with hashed filenames for cache busting.
- For production behind a reverse proxy (e.g., Nginx), you can serve `/static/` from the proxy and keep WhiteNoise as fallback.
