@echo off
echo Starting Douyin Downloader Web App...

:: Start Backend
start "Douyin Backend" cmd /k "cd backend && python app.py"

:: Start Frontend
start "Douyin Frontend" cmd /k "cd frontend && npm run dev"

echo Web App started!
echo Frontend: http://localhost:5173
echo Backend: http://localhost:5000
