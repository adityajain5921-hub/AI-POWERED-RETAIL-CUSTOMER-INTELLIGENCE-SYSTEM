@echo off
title Retail Customer Intelligence Dashboard
echo =========================================================
echo Starting Retail Customer Intelligence Dashboard...
echo - Simple College UI: http://127.0.0.1:5000
echo - Modern SaaS UI:    http://127.0.0.1:5000/modern
echo =========================================================
cd /d "%~dp0"
echo Opening browser at http://127.0.0.1:5000
start "" "http://127.0.0.1:5000"
python app.py
pause
