@echo off
REM Start Backend Server for Douyin Downloader

echo ========================================
echo   Douyin Downloader - Backend Server
echo ========================================
echo.

cd backend
echo Starting Flask server on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
