@echo off
title SATRIA SE2026
cd /d "%~dp0"

echo ============================================================
echo   SATRIA SE2026 - Mempersiapkan aplikasi...
echo ============================================================

echo.
echo Memeriksa database MySQL/XAMPP...
tasklist /FI "IMAGENAME eq mysqld.exe" 2>NUL | find /I "mysqld.exe" >NUL
if errorlevel 1 (
    if exist "C:\xampp\mysql_start.bat" (
        echo Database belum menyala, menyalakan MySQL lewat XAMPP...
        start "MySQL - SATRIA SE2026" "C:\xampp\mysql_start.bat"
        echo Menunggu MySQL siap...
        timeout /t 6 /nobreak >nul
    ) else (
        echo [PERINGATAN] MySQL belum terdeteksi menyala dan XAMPP tidak
        echo ditemukan di C:\xampp. Kalau aplikasi gagal konek ke database,
        echo nyalakan MySQL/MariaDB secara manual dulu.
    )
) else (
    echo Database sudah menyala.
)

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [Setup awal - hanya sekali] Menyiapkan Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [GAGAL] Python tidak ditemukan. Pastikan Python 3.10+ sudah
        echo ter-install dan bisa dipanggil lewat perintah "python" di PC ini.
        pause
        exit /b 1
    )

    echo [Setup awal - hanya sekali] Menginstal komponen aplikasi ^(bisa beberapa menit^)...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [GAGAL] Instalasi komponen aplikasi gagal. Periksa pesan error di atas.
        pause
        exit /b 1
    )
)

echo.
echo Menjalankan server...
echo.
".venv\Scripts\python.exe" serve.py

echo.
echo ============================================================
echo   Server berhenti.
echo ============================================================
pause
