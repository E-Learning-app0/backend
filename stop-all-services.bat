@echo off
REM stop-all-services.bat - Stop all E-Learning services for Windows

echo 🛑 Stopping E-Learning Application...
echo ==========================

echo 🌐 Stopping NGINX Gateway...
C:\nginx-1.29.0\nginx.exe -s quit 2>nul || echo    NGINX not running

echo 🧹 Stopping all Python services...
taskkill /f /im python.exe 2>nul || echo    No Python processes found

echo 🧹 Cleaning up any remaining processes on our ports...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8001" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8002" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul  
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8005" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul

echo ✅ All services stopped!
echo ==========================

pause
