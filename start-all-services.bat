@echo off
REM start-all-services.bat - Start all E-Learning services for Windows

echo 🚀 Starting E-Learning Application...
echo ==========================

echo 🔍 Checking if ports are available...
netstat -an | find "8000" | find "LISTENING" >nul && (
    echo ⚠️  Port 8000 is already in use
    pause
    exit /b 1
)

netstat -an | find "8001" | find "LISTENING" >nul && (
    echo ⚠️  Port 8001 is already in use  
    pause
    exit /b 1
)

netstat -an | find "8002" | find "LISTENING" >nul && (
    echo ⚠️  Port 8002 is already in use
    pause
    exit /b 1
)

REM Skipping port 8005 check - Payment Service not in use yet

echo ✅ All ports are available

echo.
echo 🎯 Starting services...

echo 🔐 Starting Auth Service on port 8001...
cd auth-service
start /b venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001
cd ..

timeout /t 3 /nobreak >nul

echo 📚 Starting Content Service on port 8002...
cd content-service
start /b env\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8002  
cd ..

timeout /t 3 /nobreak >nul

REM Payment Service - Not in use yet, will implement later
REM echo 💳 Starting Payment Service on port 8005...
REM cd payment-service
REM if exist venv (
REM     start /b venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8005
REM ) else (
REM     echo ⚠️  Payment service virtual environment not found. Creating one...
REM     python -m venv venv
REM     venv\Scripts\pip.exe install -r requirements.txt
REM     start /b venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8005
REM )
REM cd ..

echo ⏳ Waiting for services to start...
timeout /t 5 /nobreak >nul

echo 🌐 Starting NGINX Gateway on port 8000...
if not exist logs mkdir logs
C:\nginx-1.29.0\nginx.exe -c "C:\Users\ASUS\Desktop\E-learning_app\backend\nginx.conf"

echo.
echo ✅ All services started successfully!
echo ==========================
echo 🌐 API Gateway:      http://localhost:8000
echo 🔐 Auth Service:     http://localhost:8001
echo 📚 Content Service:  http://localhost:8002  
REM echo 💳 Payment Service:  http://localhost:8005 (Not implemented yet)
echo 🤖 Port 8004:        Reserved for your agent service
echo.
echo 🔑 Frontend API Base: http://localhost:8000/api/v1
echo 🔄 Token Refresh:     POST http://localhost:8000/api/v1/refresh
echo 💡 Payment Service:   Will be implemented later
echo.
echo To stop all services: stop-all-services.bat

pause
