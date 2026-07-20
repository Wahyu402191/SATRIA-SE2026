"""
Script untuk membersihkan berita yang tidak relevan dengan Sensus Ekonomi 2026
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from db_config import get_connection

WIB = ZoneInfo('Asia/Jakarta')

# Blacklist keywords - berita yang mengandung ini akan dihapus
BLACKLIST_KEYWORDS = [
    'kripto',
    'bitcoin',
    'ethereum',
    'saham',
    'bursa efek',
    'forex',
    'trading',
    'investasi saham',
    'restrukturisasi utang',
    'whoosh',
    'kereta cepat',
    'konflik',
    'perang',
    'israel',
    'iran',
    'musik festival',
    'bromo sunset music',
    'film',
    'artis',
    'selebriti',
    'wabup dompu',
    'tinggalkan sidang',
]

# Required keywords - setidaknya satu harus ada
REQUIRED_KEYWORDS = [
    'sensus ekonomi',
    'se2026',
    'se 2026',
]

def is_relevant_article(title, content):
    """Cek apakah artikel relevan dengan Sensus Ekonomi 2026"""
    text = (title + ' ' + (content or '')).lower()
    
    # Cek blacklist dulu
    for blackword in BLACKLIST_KEYWORDS:
        if blackword in text:
            return False
    
    # Cek apakah ada keyword yang required
    has_required = False
    for keyword in REQUIRED_KEYWORDS:
        if keyword in text:
            has_required = True
            break
    
    return has_required


def main():
    print("="*60)
    print("🧹 MEMBERSIHKAN BERITA TIDAK RELEVAN")
    print("="*60)
    
    # Connect to database
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all articles
    print("\n[1] Mengambil semua artikel dari database...")
    cursor.execute("""
        SELECT id, title, content, rss_snippet 
        FROM se_news_articles 
        ORDER BY published_date DESC
    """)
    
    all_articles = cursor.fetchall()
    print(f"  Total artikel di database: {len(all_articles)}")
    
    # Check relevance
    print("\n[2] Memeriksa relevansi artikel...")
    irrelevant_ids = []
    relevant_count = 0
    
    for article_id, title, content, snippet in all_articles:
        text_content = content or snippet or ''
        if not is_relevant_article(title, text_content):
            irrelevant_ids.append(article_id)
            print(f"  ✗ ID {article_id}: {title[:60]}...")
        else:
            relevant_count += 1
    
    print(f"\n📊 Hasil pemeriksaan:")
    print(f"  ✓ Artikel relevan: {relevant_count}")
    print(f"  ✗ Artikel tidak relevan: {len(irrelevant_ids)}")
    
    # Delete irrelevant articles
    if irrelevant_ids:
        print(f"\n[3] Menghapus {len(irrelevant_ids)} artikel tidak relevan...")
        placeholders = ','.join(['%s'] * len(irrelevant_ids))
        cursor.execute(f"""
            DELETE FROM se_news_articles 
            WHERE id IN ({placeholders})
        """, irrelevant_ids)
        conn.commit()
        print(f"  ✓ Berhasil dihapus: {len(irrelevant_ids)} artikel")
    else:
        print("\n✓ Tidak ada artikel yang perlu dihapus")
    
    # Show final stats
    cursor.execute("SELECT COUNT(*) FROM se_news_articles")
    final_count = cursor.fetchone()[0]
    
    print(f"\n{'='*60}")
    print("✅ PEMBERSIHAN SELESAI")
    print(f"{'='*60}")
    print(f"Total artikel tersisa: {final_count}")
    print("Semua artikel sekarang relevan dengan Sensus Ekonomi 2026")
    
    conn.close()


if __name__ == '__main__':
    main()
