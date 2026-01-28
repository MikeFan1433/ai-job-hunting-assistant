#!/bin/bash

# Start Frontend
echo "🚀 Starting Frontend..."
echo "📍 Frontend will be available at http://localhost:3000"
echo ""

cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

npm run dev
