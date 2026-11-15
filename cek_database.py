"""
Script untuk mengecek isi database SATRIA SE2026
Memverifikasi apakah tabel sudah terisi dengan benar
"""

import mysql.connector
from mysql.connector import Error

def check_database():
    """Cek semua tabel di database dan tampilkan jumlah datanya"""
    
    print("="*70)
    print("  CEK DATABASE SATRIA SE2026")
    print("="*70)
    print()
    
    try:
        # Koneksi ke database
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='satria_se2026'
        )
        
        if conn.is_connected():
            print("[OK] Koneksi ke database berhasil!")
            print(f"     Database: satria_se2026")
            print()
            
            cursor = conn.cursor()
            
            # Daftar tabel yang harus ada
            tables_to_check = [
                ('videos', 'Data Video YouTube'),
                ('comments', 'Komentar YouTube'),
                ('analysis_results', 'Hasil Analisis YouTube'),
                ('analysis_sessions', 'Sesi Analisis YouTube'),
                ('news_articles', 'Berita Media Massa'),
                ('news_sources', 'Sumber Media Massa'),
                ('news_analysis_results', 'Hasil Analisis Media Massa'),
                ('se_news_articles', 'Berita Sensus Ekonomi 2026'),
                ('se_news_sentiment', 'Sentimen Berita SE2026'),
                ('se_news_fetch_log', 'Log Pengambilan Berita SE2026'),
                ('users', 'Pengguna/User Accounts'),
            ]
            
            print("="*70)
            print(f"{'Tabel':<30} {'Jumlah Data':<15} {'Status':<25}")
            print("-"*70)
            
            total_data = 0
            empty_tables = []
            missing_tables = []
            
            for table_name, description in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    count = cursor.fetchone()[0]
                    total_data += count
                    
                    if count == 0:
                        status = "[KOSONG]"
                        empty_tables.append(table_name)
                    elif count < 10:
                        status = "[SEDIKIT DATA]"
                    else:
                        status = "[OK]"
                    
                    print(f"{table_name:<30} {count:>10,}     {status:<25}")
                    
                except Error as e:
                    if "doesn't exist" in str(e):
                        print(f"{table_name:<30} {'N/A':>10}     [TABEL TIDAK ADA]")
                        missing_tables.append(table_name)
                    else:
                        print(f"{table_name:<30} {'ERROR':>10}     [ERROR: {e}]")
            
            print("-"*70)
            print(f"{'TOTAL DATA':<30} {total_data:>10,}")
            print("="*70)
            print()
            
            # Ringkasan
            print("RINGKASAN:")
            print("-"*70)
            
            if missing_tables:
                print(f"[!] Tabel yang hilang ({len(missing_tables)}): {', '.join(missing_tables)}")
                print("    Solusi: Import ulang file 'satria_se2026 (1).sql'")
                print()
            
            if empty_tables and not missing_tables:
                print(f"[!] Tabel kosong ({len(empty_tables)}): {', '.join(empty_tables)}")
                print("    Ini normal jika belum pernah scraping/analisis")
                print()
            
            if not missing_tables and not empty_tables:
                print("[OK] Semua tabel sudah terisi dengan baik!")
                print()
            
            if total_data > 1000:
                print(f"[OK] Database berisi {total_data:,} baris data total")
                print("[OK] Aplikasi siap digunakan!")
            elif total_data > 0:
                print(f"[INFO] Database berisi {total_data:,} baris data")
                print("[INFO] Beberapa fitur mungkin belum memiliki data")
            else:
                print("[WARNING] Database masih kosong!")
                print("[ACTION] Import file 'satria_se2026 (1).sql' via phpMyAdmin")
            
            print()
            
            # Cek khusus untuk berita SE2026 (harus banyak)
            cursor.execute("SELECT COUNT(*) FROM `se_news_articles`")
            se_news_count = cursor.fetchone()[0]
            
            if se_news_count > 1000:
                print(f"[OK] Berita Sensus Ekonomi 2026: {se_news_count:,} artikel")
                print("[OK] Halaman 'Berita SE2026' akan menampilkan data lengkap")
            elif se_news_count > 0:
                print(f"[WARNING] Berita SE2026 hanya {se_news_count} artikel")
                print("[INFO] Seharusnya ada ribuan artikel jika import berhasil")
            else:
                print("[ERROR] Tidak ada data Berita SE2026!")
                print("[ACTION] Pastikan import 'satria_se2026 (1).sql' berhasil")
            
            print()
            print("="*70)
            
            cursor.close()
            conn.close()
            
    except Error as e:
        print(f"[ERROR] Koneksi database gagal: {e}")
        print()
        print("Solusi:")
        print("1. Pastikan MySQL/XAMPP sudah running")
        print("2. Pastikan database 'satria_se2026' sudah dibuat")
        print("3. Pastikan file 'satria_se2026 (1).sql' sudah di-import")
        print()

if __name__ == "__main__":
    try:
        check_database()
        input("\nTekan Enter untuk keluar...")
    except KeyboardInterrupt:
        print("\n\nDibatalkan oleh user")
    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}")
        import traceback
        traceback.print_exc()
        input("\nTekan Enter untuk keluar...")
