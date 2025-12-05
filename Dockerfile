FROM python:3.11-slim

LABEL maintainer="Bouncer Team"
LABEL description="Bouncer - AI-powered file monitoring agent"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create bouncer directories
RUN mkdir -p .bouncer/logs .bouncer/audit

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "main.py", "start"]
