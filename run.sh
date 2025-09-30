#!/bin/bash

# Admin Portal Startup Script
echo "🚀 Admin Portal Setup & Start"
echo "================================"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install Poetry first:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ] && [ ! -f "poetry.lock" ]; then
    echo "📦 Installing dependencies..."
    poetry install
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your API keys (optional)"
fi

# Create uploads directory
mkdir -p uploads

echo ""
echo "🌐 Starting server..."
echo "📍 URL: http://localhost:8080"
echo "👤 Admin: admin1 / 1234"
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Start the application
poetry run python start.py