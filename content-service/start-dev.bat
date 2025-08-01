@echo off
REM Development startup script for Content Service (Windows)

echo 🚀 Starting Content Service...

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo 📝 Please edit .env file with your actual configuration values
    echo 🔑 Important: Update DATABASE_URL
)

REM Install dependencies if needed
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Start the server
echo 🌟 Starting Content Service on http://localhost:8002
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
