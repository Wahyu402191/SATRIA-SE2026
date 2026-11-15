@echo off
chcp 65001 > nul
title Buat Data Dummy SATRIA SE2026

echo ============================================================
echo   GENERATOR DATA DUMMY SATRIA SE2026
echo ============================================================
echo.
echo Script ini akan membuat data dummy untuk:
echo - YouTube: Video dan Komentar
echo - Media Massa: Artikel Berita
echo - Berita SE2026: Artikel Sensus Ekonomi
echo - User Accounts untuk Login
echo.
echo ============================================================
echo.

python buat_data_dummy_lengkap.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Gagal menjalankan script!
    echo Pastikan Python sudah terinstall.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Setelah data dummy dibuat, restart aplikasi dengan:
echo   Jalankan_SATRIA_SE2026.bat
echo ============================================================
pause
