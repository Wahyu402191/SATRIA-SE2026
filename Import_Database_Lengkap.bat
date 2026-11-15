@echo off
chcp 65001 > nul
title Import Database SATRIA SE2026 - Lengkap

echo ================================================
echo   IMPORT DATABASE SATRIA SE2026 (LENGKAP)
echo ================================================
echo.

set MYSQL_PATH=C:\xampp\mysql\bin
set DB_NAME=satria_se2026
set SQL_FILE=satria_se2026 (1).sql

echo Memeriksa file SQL...
if not exist "%SQL_FILE%" (
    echo [ERROR] File "%SQL_FILE%" tidak ditemukan!
    echo Pastikan file ada di folder yang sama dengan script ini.
    pause
    exit /b 1
)

echo File ditemukan: %SQL_FILE%
echo Ukuran file: 
for %%A in ("%SQL_FILE%") do echo %%~zA bytes (sekitar 18 MB)
echo.

echo Memeriksa MySQL...
if not exist "%MYSQL_PATH%\mysql.exe" (
    echo [ERROR] MySQL tidak ditemukan di %MYSQL_PATH%
    echo Pastikan XAMPP sudah terinstall dengan benar.
    pause
    exit /b 1
)

echo MySQL ditemukan!
echo.

echo Memeriksa apakah MySQL sudah berjalan...
tasklist /FI "IMAGENAME eq mysqld.exe" 2>NUL | find /I /N "mysqld.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo MySQL sudah berjalan.
) else (
    echo MySQL belum berjalan. Menjalankan MySQL...
    start "" "%MYSQL_PATH%\..\mysql_start.bat"
    timeout /t 5 /nobreak > nul
    echo MySQL telah dijalankan.
)
echo.

echo ================================================
echo MEMULAI IMPORT DATABASE
echo ================================================
echo Database: %DB_NAME%
echo File: %SQL_FILE%
echo.
echo CATATAN: Proses ini akan memakan waktu 1-3 menit
echo          karena file berukuran 18 MB.
echo          Jangan tutup jendela ini!
echo ================================================
echo.

echo Membuat database jika belum ada...
"%MYSQL_PATH%\mysql.exe" -u root -e "CREATE DATABASE IF NOT EXISTS %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Gagal membuat database!
    echo Pastikan MySQL berjalan dengan benar.
    pause
    exit /b 1
)

echo Database %DB_NAME% siap.
echo.

echo Mengimport data dari %SQL_FILE%...
echo Mohon tunggu...
echo.

"%MYSQL_PATH%\mysql.exe" -u root %DB_NAME% < "%SQL_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo   IMPORT BERHASIL!
    echo ================================================
    echo Database %DB_NAME% telah berisi data lengkap.
    echo.
    echo Anda bisa cek di phpMyAdmin:
    echo - Buka http://localhost/phpmyadmin
    echo - Pilih database: %DB_NAME%
    echo - Cek tabel-tabel yang sudah terisi
    echo.
    echo Aplikasi SATRIA SE2026 siap digunakan!
    echo ================================================
) else (
    echo.
    echo ================================================
    echo   IMPORT GAGAL!
    echo ================================================
    echo Terjadi kesalahan saat import.
    echo.
    echo Solusi:
    echo 1. Pastikan MySQL berjalan
    echo 2. Pastikan file SQL tidak corrupt
    echo 3. Coba import manual via phpMyAdmin
    echo ================================================
)

echo.
pause
