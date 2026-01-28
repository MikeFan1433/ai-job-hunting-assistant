#!/bin/bash

# Production deployment script
# This script starts the application in production mode

set -e

echo "🚀 Starting AI Job Hunting Assistant in production mode..."
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if frontend is built
if [ ! -d "frontend/dist" ]; then
    echo "⚠️  Frontend not built. Running build script..."
    ./build.sh
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./build.sh first."
    exit 1
fi

source venv/bin/activate

# Get host and port from environment or use defaults
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}

echo "📍 Starting server on http://${HOST}:${PORT}"
echo "👥 Workers: ${WORKERS}"
echo ""
echo "🌐 Access the application at:"
echo "   - Local: http://localhost:${PORT}"
if [ "$HOST" = "0.0.0.0" ]; then
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' || echo "your-ip")
    echo "   - Network: http://${LOCAL_IP}:${PORT}"
fi
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
if command -v gunicorn &> /dev/null; then
    # Use gunicorn for production (better for production)
    echo "🐘 Starting with Gunicorn (production mode)..."
    gunicorn workflow_api:app \
        --workers ${WORKERS} \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind ${HOST}:${PORT} \
        --timeout 300 \
        --access-logfile - \
        --error-logfile -
else
    # Fallback to uvicorn
    echo "⚡ Starting with Uvicorn..."
    python3 -m uvicorn workflow_api:app \
        --host ${HOST} \
        --port ${PORT} \
        --workers ${WORKERS} \
        --no-reload
fi
