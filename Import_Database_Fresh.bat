@echo off
chcp 65001 > nul
title Import Database SATRIA SE2026 - Fresh Install

echo ================================================
echo   IMPORT DATABASE SATRIA SE2026 (FRESH)
echo ================================================
echo.

set MYSQL_PATH=C:\xampp\mysql\bin
set DB_NAME=satria_se2026
set SQL_FILE=satria_se2026 (1).sql

echo PERINGATAN: Script ini akan MENGHAPUS database lama
echo             dan menggantinya dengan data baru yang lengkap!
echo.
echo Database: %DB_NAME%
echo File: %SQL_FILE% (18 MB)
echo.
set /p CONFIRM="Lanjutkan? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Import dibatalkan.
    pause
    exit /b 0
)

echo.
echo Memeriksa file SQL...
if not exist "%SQL_FILE%" (
    echo [ERROR] File "%SQL_FILE%" tidak ditemukan!
    pause
    exit /b 1
)

echo [OK] File ditemukan
echo.

echo Memeriksa MySQL...
if not exist "%MYSQL_PATH%\mysql.exe" (
    echo [ERROR] MySQL tidak ditemukan di %MYSQL_PATH%
    pause
    exit /b 1
)

echo [OK] MySQL ditemukan
echo.

echo ================================================
echo LANGKAH 1: Menghapus database lama
echo ================================================
"%MYSQL_PATH%\mysql.exe" -u root -e "DROP DATABASE IF EXISTS %DB_NAME%;"
echo [OK] Database lama dihapus
echo.

echo ================================================
echo LANGKAH 2: Membuat database baru
echo ================================================
"%MYSQL_PATH%\mysql.exe" -u root -e "CREATE DATABASE %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
echo [OK] Database baru dibuat
echo.

echo ================================================
echo LANGKAH 3: Import data (tunggu 1-3 menit)
echo ================================================
echo Sedang mengimport %SQL_FILE%...
echo Jangan tutup jendela ini!
echo.

"%MYSQL_PATH%\mysql.exe" -u root %DB_NAME% < "%SQL_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo   IMPORT BERHASIL!
    echo ================================================
    echo.
    echo Database %DB_NAME% telah berisi data lengkap:
    echo - Berita Sensus Ekonomi 2026 (ribuan artikel)
    echo - Data Media Massa Indonesia
    echo - Akun pengguna untuk login
    echo - Semua tabel sudah terisi
    echo.
    echo Cek di phpMyAdmin: http://localhost/phpmyadmin
    echo.
    echo Aplikasi SATRIA SE2026 siap digunakan!
    echo Jalankan: Jalankan_SATRIA_SE2026.bat
    echo ================================================
) else (
    echo.
    echo ================================================
    echo   IMPORT GAGAL!
    echo ================================================
    echo Coba import manual via phpMyAdmin
    echo ================================================
)

echo.
pause
