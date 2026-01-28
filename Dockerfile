# Dockerfile for AI Job Hunting Assistant
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for building frontend)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Copy requirements and install Python dependencies
COPY requirements.txt .
# Install dependencies without cache to ensure fresh install
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build frontend
WORKDIR /app/frontend
RUN if [ ! -d "node_modules" ]; then \
    npm install && \
    npm run build; \
    fi

# Return to app directory
WORKDIR /app

# Create data directories
RUN mkdir -p data/resumes data/projects data/jobs data/outputs data/vector_db

# Expose port (PORT will be set at runtime by Koyeb)
EXPOSE 8000

# Health check (uses curl which is already installed, and PORT env var with default fallback)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD sh -c "port=\${PORT:-8000} && curl -f http://localhost:\${port}/api/v1/health || exit 1"

# Start server using PORT environment variable
# Use shell form (sh -c) to ensure environment variable expansion works correctly
# Critical: PORT is set by Koyeb at runtime, default to 8000 if not set
CMD sh -c "gunicorn workflow_api:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 300 --access-logfile - --error-logfile -"
