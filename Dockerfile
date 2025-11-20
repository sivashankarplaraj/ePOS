# Stage 1: Base build stage
FROM python:3.13-slim 
# Set the working directory in the container
WORKDIR /ePOS

# # Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy requirements and install (upgrade pip + deps in one layer for cache efficiency)
COPY requirements.txt .
RUN pip install --upgrade pip && \
	pip install --no-cache-dir -r requirements.txt

# Copy application code from ePOS directory to /ePOS in container
COPY . .

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Collect static files (ensure settings module defined)
ENV DJANGO_SETTINGS_MODULE=epos.settings
RUN python manage.py collectstatic --noinput

EXPOSE 8090

# Simplified runtime (gunicorn HTTP). Remove TLS complexity.
ENV BIND_ADDR=0.0.0.0:8090

# Healthcheck for container orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python -c "import urllib.request,sys;\n try: urllib.request.urlopen('http://127.0.0.1:8090/'); sys.exit(0)\n except Exception: sys.exit(1)"

CMD ["gunicorn", "epos.wsgi:application", "--bind", "0.0.0.0:8090", "--workers", "3"]

