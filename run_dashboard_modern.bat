@echo off
title RetailPulse AI - Modern SaaS Version
echo =========================================================
echo Starting Modern SaaS Version of Retail Intelligence...
echo =========================================================
cd /d "%~dp0"
echo Opening browser at http://127.0.0.1:5000/modern
start "" "http://127.0.0.1:5000/modern"
python app.py
pause
