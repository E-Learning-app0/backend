@echo off
echo 🧹 Cleaning up E-Learning Backend...
echo ==========================

echo 🗑️ Removing unnecessary files and directories...

REM Remove old API Gateway (we're using NGINX now)
if exist "api-gateway" (
    echo    ❌ Removing old api-gateway directory...
    rmdir /s /q "api-gateway"
)

REM Remove old Docker configurations (we're using direct deployment)
if exist "docker-compose.kong.yml" (
    echo    ❌ Removing docker-compose.kong.yml...
    del "docker-compose.kong.yml"
)

if exist "docker-compose.traefik.yml" (
    echo    ❌ Removing docker-compose.traefik.yml...
    del "docker-compose.traefik.yml"
)

REM Remove duplicate/old startup scripts
if exist "start-all-services.sh" (
    echo    ❌ Removing start-all-services.sh (Linux script)...
    del "start-all-services.sh"
)

if exist "stop-all-services.sh" (
    echo    ❌ Removing stop-all-services.sh (Linux script)...
    del "stop-all-services.sh"
)

if exist "start-nginx-gateway.bat" (
    echo    ❌ Removing start-nginx-gateway.bat (redundant)...
    del "start-nginx-gateway.bat"
)

if exist "start-nginx-gateway.sh" (
    echo    ❌ Removing start-nginx-gateway.sh (Linux script)...
    del "start-nginx-gateway.sh"
)

if exist "start-nginx.bat" (
    echo    ❌ Removing start-nginx.bat (redundant)...
    del "start-nginx.bat"
)

if exist "start-services-only.bat" (
    echo    ❌ Removing start-services-only.bat (redundant)...
    del "start-services-only.bat"
)

if exist "stop-nginx.bat" (
    echo    ❌ Removing stop-nginx.bat (redundant)...
    del "stop-nginx.bat"
)


REM Clean up log files (keep directory structure)
if exist "logs" (
    echo    🧹 Cleaning log files...
    if exist "logs\access.log" del "logs\access.log"
    if exist "logs\error.log" del "logs\error.log"
    if exist "logs\nginx.pid" del "logs\nginx.pid"
)

REM Remove .env.template (you should have real .env files)
if exist ".env.template" (
    echo    ❌ Removing .env.template...
    del ".env.template"
)

echo.
echo ✅ Cleanup completed!
echo ==========================
echo 🎯 Kept essential files:
echo    ✅ start-all-services.bat
echo    ✅ stop-all-services.bat  
echo    ✅ nginx.conf
echo    ✅ auth-service/
echo    ✅ content-service/
echo    ✅ payment-service/
echo    ✅ Documentation files
echo.
echo 🗂️ Your backend is now clean and organized!

pause
