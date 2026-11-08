@echo off
setlocal
cd /d "%~dp0"
title Elektronik Store - JANGAN tutup jendela ini selama aplikasi dipakai
if not exist venv\Scripts\python.exe (
    echo Jalankan setup.bat dulu.
    pause
    exit /b 1
)
venv\Scripts\python scripts\lokal.py jalankan
pause
