@echo off
echo Starting SignVani Full Stack Application...
echo.

REM Start Backend API Server
echo Starting Backend API Server on port 8000...
start "Backend API" cmd /k "cd /d %~dp0nlp_backend && python api_server.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start Frontend Development Server
echo Starting Frontend on port 3000...
start "Frontend" cmd /k "cd /d %~dp0client && npm start"

echo.
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo Enhanced Convert Page: http://localhost:3000/sign-kit/convert-enhanced
echo.
echo Press any key to exit...
pause >nul
