FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for evdev (for USB HID mode)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libudev-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Flask for the test API
RUN pip install --no-cache-dir flask

RUN apt-get update && apt-get install -y python3-pygame

# Copy application code
COPY . .

# Create directories for mounted volumes
RUN mkdir -p /app/config /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TEST_MODE=false

# Expose port for test API
EXPOSE 5000

# Run the test API by default
# Use environment variable to determine which script to run
CMD if [ "$TEST_MODE" = "true" ]; then python test_api.py; else python main.py; fi
# Add this to your existing Dockerfile
RUN apt-get update && apt-get install -y python3-pygame
# If you're using a slim image, you might also need these dependencies
RUN apt-get install -y libsdl2-2.0-0 libsdl2-mixer-2.0-0
