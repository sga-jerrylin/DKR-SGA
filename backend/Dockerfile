# Backend Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (including ffmpeg for video processing)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    curl \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy all requirements files
COPY backend/requirements.txt ./backend_requirements.txt
COPY requirements.txt ./root_requirements.txt

# Install Python dependencies (merge both requirements)
# Use trusted-host to bypass SSL certificate issues
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r root_requirements.txt && \
    pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r backend_requirements.txt

# Copy startup script first
COPY backend/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy visual_memvid module (from project root)
COPY visual_memvid ./visual_memvid

# Copy backend application code
COPY backend ./

# Create necessary directories
RUN mkdir -p /app/data/documents /app/data/videos /app/data/summaries \
    /app/data/indexes /app/data/temp /app/data/cache /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application with startup script
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

