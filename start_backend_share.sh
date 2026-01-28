#!/bin/bash

# Start Backend API for sharing (listens on all interfaces)
echo "🚀 Starting Backend API (Shareable Mode)..."
echo "📍 API will be available at:"
echo "   - http://localhost:8000 (local)"
echo "   - http://$(hostname -I | awk '{print $1}'):8000 (network)"
echo ""
echo "💡 Share the network URL with others on the same network"
echo ""

cd "$(dirname "$0")"
python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000 --reload
