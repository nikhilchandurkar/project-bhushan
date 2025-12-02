# Use Python slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (Postgres, Redis, netcat) and keep image small
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/
COPY .env /app/

# Copy startup script and make it executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Collect static files, compress, and run migrations (optional in prod build)
# Uncomment if you want them baked into the image
# RUN python manage.py collectstatic --noinput && \
#     python manage.py compress && \
#     python manage.py migrate

# Expose the port
EXPOSE 8000

# Start container with startup script
CMD ["/app/start.sh"]
