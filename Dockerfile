FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable live output streaming
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for audio decoding, soundfile, and Tkinter desktop GUI
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    python3-tk \
    tk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python audio DSP dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and sample data
COPY . .

# Create volume mount point for host audio sharing
VOLUME ["/data"]

# Default entrypoint runs the main application
CMD ["python", "main.py"]
