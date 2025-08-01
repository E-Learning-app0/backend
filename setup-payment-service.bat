@echo off
echo 🔧 Setting up Payment Service Virtual Environment...

cd payment-service

if exist venv (
    echo ✅ Virtual environment already exists
) else (
    echo 🔨 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
)

echo 📦 Installing dependencies...
venv\Scripts\pip.exe install -r requirements.txt

echo ✅ Payment service setup complete!
cd ..
pause
