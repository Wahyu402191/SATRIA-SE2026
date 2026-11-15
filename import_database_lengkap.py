"""
Script untuk import database SATRIA SE2026 yang lengkap
File: satria_se2026 (1).sql (18 MB dengan data lengkap)
"""

import os
import subprocess
import sys
from pathlib import Path

def check_file_exists(filepath):
    """Cek apakah file SQL ada"""
    if not os.path.exists(filepath):
        print(f"[ERROR] File tidak ditemukan: {filepath}")
        return False
    
    file_size = os.path.getsize(filepath)
    print(f"[OK] File ditemukan: {filepath}")
    print(f"     Ukuran: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    return True

def check_mysql_running():
    """Cek apakah MySQL sudah berjalan"""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq mysqld.exe'],
            capture_output=True,
            text=True
        )
        return 'mysqld.exe' in result.stdout
    except Exception as e:
        print(f"[WARNING] Tidak dapat memeriksa status MySQL: {e}")
        return False

def start_mysql():
    """Jalankan MySQL jika belum berjalan"""
    mysql_path = Path("C:/xampp/mysql/bin")
    
    if not mysql_path.exists():
        print(f"[ERROR] MySQL tidak ditemukan di {mysql_path}")
        print("        Pastikan XAMPP sudah terinstall dengan benar.")
        return False
    
    if check_mysql_running():
        print("[OK] MySQL sudah berjalan")
        return True
    
    print("[INFO] MySQL belum berjalan. Menjalankan MySQL...")
    try:
        # Coba jalankan MySQL via mysqld
        subprocess.Popen(
            [str(mysql_path / "mysqld.exe")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        import time
        time.sleep(5)  # Tunggu MySQL start
        
        if check_mysql_running():
            print("[OK] MySQL berhasil dijalankan")
            return True
        else:
            print("[WARNING] MySQL mungkin belum sepenuhnya siap")
            return True  # Lanjutkan saja
    except Exception as e:
        print(f"[ERROR] Gagal menjalankan MySQL: {e}")
        print("        Silakan jalankan MySQL secara manual dari XAMPP Control Panel")
        return False

def create_database(mysql_path, db_name):
    """Buat database jika belum ada"""
    print(f"\n[INFO] Membuat database '{db_name}' jika belum ada...")
    
    try:
        cmd = [
            str(mysql_path / "mysql.exe"),
            "-u", "root",
            "-e", f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"[OK] Database '{db_name}' siap")
            return True
        else:
            print(f"[ERROR] Gagal membuat database: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Exception saat membuat database: {e}")
        return False

def import_sql_file(mysql_path, db_name, sql_file):
    """Import file SQL ke database"""
    print(f"\n{'='*60}")
    print(f"  MEMULAI IMPORT DATABASE")
    print(f"{'='*60}")
    print(f"Database: {db_name}")
    print(f"File: {sql_file}")
    print(f"\nCATATAN: Proses ini akan memakan waktu 1-3 menit")
    print(f"         karena file berukuran 18 MB.")
    print(f"         Jangan tutup program ini!")
    print(f"{'='*60}\n")
    
    try:
        cmd = [
            str(mysql_path / "mysql.exe"),
            "-u", "root",
            db_name
        ]
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdin=f,
                capture_output=True,
                text=True
            )
        
        if result.returncode == 0:
            print(f"\n{'='*60}")
            print(f"  IMPORT BERHASIL!")
            print(f"{'='*60}")
            print(f"Database '{db_name}' telah berisi data lengkap.")
            print(f"\nAnda bisa cek di phpMyAdmin:")
            print(f"- Buka http://localhost/phpmyadmin")
            print(f"- Pilih database: {db_name}")
            print(f"- Cek tabel-tabel yang sudah terisi")
            print(f"\nAplikasi SATRIA SE2026 siap digunakan!")
            print(f"{'='*60}")
            return True
        else:
            print(f"\n{'='*60}")
            print(f"  IMPORT GAGAL!")
            print(f"{'='*60}")
            print(f"Error: {result.stderr}")
            print(f"\nSolusi:")
            print(f"1. Pastikan MySQL berjalan")
            print(f"2. Pastikan file SQL tidak corrupt")
            print(f"3. Coba import manual via phpMyAdmin")
            print(f"{'='*60}")
            return False
    except Exception as e:
        print(f"\n[ERROR] Exception saat import: {e}")
        return False

def main():
    """Fungsi utama"""
    print("="*60)
    print("  IMPORT DATABASE SATRIA SE2026 (LENGKAP)")
    print("="*60)
    print()
    
    # Konfigurasi
    mysql_path = Path("C:/xampp/mysql/bin")
    db_name = "satria_se2026"
    sql_file = "satria_se2026 (1).sql"
    
    # 1. Cek file SQL
    if not check_file_exists(sql_file):
        input("\nTekan Enter untuk keluar...")
        sys.exit(1)
    
    print()
    
    # 2. Cek dan jalankan MySQL
    if not start_mysql():
        input("\nTekan Enter untuk keluar...")
        sys.exit(1)
    
    print()
    
    # 3. Buat database
    if not create_database(mysql_path, db_name):
        input("\nTekan Enter untuk keluar...")
        sys.exit(1)
    
    # 4. Import SQL file
    if not import_sql_file(mysql_path, db_name, sql_file):
        input("\nTekan Enter untuk keluar...")
        sys.exit(1)
    
    print()
    input("Tekan Enter untuk keluar...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Import dibatalkan oleh user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}")
        import traceback
        traceback.print_exc()
        input("\nTekan Enter untuk keluar...")
        sys.exit(1)
