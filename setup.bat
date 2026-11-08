@echo off
setlocal
cd /d "%~dp0"
title Setup Elektronik Store
echo ==========================================================
echo   SETUP ELEKTRONIK STORE (cukup sekali per laptop)
echo ==========================================================

python --version >nul 2>nul
if errorlevel 1 goto tanpa_python
python -c "import sys; sys.exit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) else 1)"
if errorlevel 1 goto versi_python

if not exist venv\Scripts\python.exe (
    echo [1/3] Membuat virtual environment venv\ ...
    python -m venv venv
    if errorlevel 1 goto gagal
)
echo [2/3] Memasang library Python dari requirements.txt ...
venv\Scripts\python -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 goto gagal

echo [3/3] Menyiapkan database, tabel, produk contoh, dan akun admin ...
venv\Scripts\python scripts\lokal.py setup
if errorlevel 1 goto gagal

echo.
echo ==========================================================
echo   SETUP SELESAI. Klik dua kali jalankan.bat untuk membuka toko.
echo ==========================================================
pause
exit /b 0

:tanpa_python
echo [X] Python belum terpasang.
echo     Unduh Python 3.12 di https://www.python.org/downloads/
echo     Saat instal, CENTANG "Add python.exe to PATH", lalu jalankan setup.bat lagi.
pause
exit /b 1

:versi_python
echo [X] Butuh Python 3.11 sampai 3.13. Versi di laptop ini:
python --version
pause
exit /b 1

:gagal
echo.
echo [X] Setup gagal. Baca pesan error di atas (lihat juga docs\INSTALASI.md bagian 6).
pause
exit /b 1
