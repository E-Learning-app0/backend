@echo off
REM Development startup script for Auth Service (Windows)

echo 🚀 Starting Auth Service...

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo 📝 Please edit .env file with your actual configuration values
    echo 🔑 Important: Update SECRET_KEY, DATABASE_URL, and email settings
)

REM Install dependencies if needed
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Run database migrations
echo 🗄️  Running database migrations...
alembic upgrade head

REM Start the server
echo 🌟 Starting Auth Service on http://localhost:8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
