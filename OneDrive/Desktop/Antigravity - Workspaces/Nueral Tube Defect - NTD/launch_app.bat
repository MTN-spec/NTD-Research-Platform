@echo off
echo ============================================================
echo   NTD Risk Prediction Web Application
echo   Starting Flask server...
echo ============================================================
echo.
echo   Once started, open your browser to: http://localhost:5000
echo   Press Ctrl+C to stop the server.
echo.
cd /d "%~dp0webapp"
py -3 app.py
pause
