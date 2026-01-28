#!/bin/bash

# Start Backend API
echo "🚀 Starting Backend API..."
echo "📍 API will be available at:"
echo "   - http://localhost:8000 (local)"
echo "   - http://$(hostname -I 2>/dev/null | awk '{print $1}' || ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}'):8000 (network)"
echo ""

cd "$(dirname "$0")"
python3 -m uvicorn workflow_api:app --host 0.0.0.0 --reload --port 8000
