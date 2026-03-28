FROM python:3.11-slim

WORKDIR /app

# Install system deps for git and postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/webhooks/ /app/

# Create workspaces directory
RUN mkdir -p /app/workspaces/mirrors /app/workspaces/runs

EXPOSE 8000

# Default: run the API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
