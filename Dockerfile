# Use a lightweight Python image as the base (aligned with README Python 3.13)
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy requirements and install (upgrade pip + deps in one layer for cache efficiency)
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
	pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . /app/

# Optional: openssl kept for legacy start.sh TLS; remove to slim further
RUN apt-get update && apt-get install -y --no-install-recommends openssl && rm -rf /var/lib/apt/lists/*

# Collect static files (ensure settings module defined)
ENV DJANGO_SETTINGS_MODULE=epos.settings
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Simplified runtime (gunicorn HTTP). Remove TLS complexity.
ENV BIND_ADDR=0.0.0.0:8000

# Healthcheck for container orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python -c "import urllib.request,sys;\n try: urllib.request.urlopen('http://127.0.0.1:8000/'); sys.exit(0)\n except Exception: sys.exit(1)"

CMD ["gunicorn", "epos.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

