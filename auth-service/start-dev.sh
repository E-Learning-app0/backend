#!/bin/bash
# Development startup script for Auth Service

echo "🚀 Starting Auth Service..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your actual configuration values"
    echo "🔑 Important: Update SECRET_KEY, DATABASE_URL, and email settings"
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Start the server
echo "🌟 Starting Auth Service on http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
