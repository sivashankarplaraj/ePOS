# Use a lightweight Python image as the base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy EPOS project files into the container
COPY . /app/

# Install openssl for optional in-container TLS (self-signed generation)
RUN apt-get update \
	&& apt-get install -y --no-install-recommends openssl \
	&& rm -rf /var/lib/apt/lists/*

# Collect static files (if applicable)
RUN python manage.py collectstatic --noinput

# Expose the port that the application will run on
EXPOSE 80

# Runtime: use start.sh to optionally enable TLS based on env vars
# Defaults: HTTP only; set USE_SSL=true to enable TLS. Provide CERT_FILE/KEY_FILE or allow self-signed generation.
ENV USE_SSL=false \
	BIND_ADDR=0.0.0.0:80 \
	CERT_FILE=/app/certs/cert.pem \
	KEY_FILE=/app/certs/key.pem

# Ensure start script is executable
RUN chmod +x /app/start.sh

# Start via helper script (TLS optional)
CMD ["/app/start.sh"]

