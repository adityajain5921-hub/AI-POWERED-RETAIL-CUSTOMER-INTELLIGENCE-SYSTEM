@echo off
title RetailPulse AI - Simple College Version
echo =========================================================
echo Starting Simple College Version of Retail Intelligence...
echo =========================================================
cd /d "%~dp0"
echo Opening browser at http://127.0.0.1:5000
start "" "http://127.0.0.1:5000"
python app.py
pause
