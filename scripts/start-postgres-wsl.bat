@echo off
REM Menyalakan PostgreSQL yang terpasang di WSL Ubuntu-24.04.
REM Biarkan jendela ini terbuka selama aplikasi dipakai (jika ditutup, WSL dan PostgreSQL ikut berhenti).
echo Menjalankan PostgreSQL di WSL (Ubuntu-24.04)...
echo Biarkan jendela ini terbuka. Tekan Ctrl+C untuk menghentikan.
wsl -d Ubuntu-24.04 -u root -- bash -c "service postgresql start && exec sleep infinity"
