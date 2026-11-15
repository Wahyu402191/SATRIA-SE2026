"""
Script untuk memperbaiki kolom published_day yang kosong
Kolom published_day adalah generated column yang mungkin tidak ter-generate otomatis
"""

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'satria_se2026'
}

print("="*70)
print("  MEMPERBAIKI KOLOM PUBLISHED_DAY")
print("="*70)
print()

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Cek berapa artikel yang published_day-nya NULL
    cursor.execute("SELECT COUNT(*) FROM se_news_articles WHERE published_day IS NULL")
    null_count = cursor.fetchone()[0]
    
    print(f"[INFO] Artikel dengan published_day NULL: {null_count}")
    
    if null_count > 0:
        print("[INFO] Memperbaiki published_day...")
        
        # Update published_day dari published_date
        cursor.execute("""
            UPDATE se_news_articles 
            SET published_day = DATE(published_date)
            WHERE published_day IS NULL
        """)
        
        conn.commit()
        print(f"[OK] {cursor.rowcount} baris diperbaiki")
    else:
        print("[OK] Semua published_day sudah terisi dengan benar")
    
    # Cek hasil
    cursor.execute("SELECT COUNT(*) FROM se_news_articles WHERE published_day IS NOT NULL")
    valid_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM se_news_articles")
    total_count = cursor.fetchone()[0]
    
    print()
    print("="*70)
    print("  HASIL")
    print("="*70)
    print(f"Total artikel: {total_count}")
    print(f"Published_day terisi: {valid_count}")
    print(f"Published_day NULL: {total_count - valid_count}")
    
    if valid_count == total_count:
        print("\n[OK] Semua artikel sudah memiliki published_day yang valid!")
        print("\nSilakan refresh halaman aplikasi (tekan F5)")
    else:
        print("\n[WARNING] Masih ada artikel tanpa published_day")
    
    print("="*70)
    
    cursor.close()
    conn.close()
    
except Error as e:
    print(f"[ERROR] {e}")

input("\nTekan Enter untuk keluar...")
