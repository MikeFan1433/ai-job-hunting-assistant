#!/bin/bash

# Build script for production deployment
# This script builds the frontend and prepares everything for deployment

set -e

echo "🏗️  Building AI Job Hunting Assistant for production..."
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Build frontend
echo "📦 Step 1: Building frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📥 Installing frontend dependencies..."
    npm install
fi

# Build frontend
echo "🔨 Building frontend (this may take a minute)..."
npm run build

if [ ! -d "dist" ]; then
    echo "❌ Frontend build failed! dist directory not found."
    exit 1
fi

echo "✅ Frontend built successfully!"
echo ""

# Step 2: Verify backend dependencies
cd ..
echo "📦 Step 2: Checking backend dependencies..."

if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo "📥 Installing/updating backend dependencies..."
    pip install -q -r requirements.txt
fi

echo "✅ Backend dependencies ready!"
echo ""

# Step 3: Summary
echo "🎉 Build complete!"
echo ""
echo "📁 Frontend build output: frontend/dist/"
echo "🚀 Ready for deployment!"
echo ""
echo "To test locally, run:"
echo "  python3 -m uvicorn workflow_api:app --host 0.0.0.0 --port 8000"
echo ""
echo "The frontend will be served automatically from the backend."
