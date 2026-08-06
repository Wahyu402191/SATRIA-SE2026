"""
Script untuk membersihkan berita yang tidak relevan dengan Sensus Ekonomi 2026
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from db_config import get_connection
from se_news_scraper import is_relevant_entry

WIB = ZoneInfo('Asia/Jakarta')


def is_relevant_article(title, snippet):
    """Cek apakah artikel relevan dengan Sensus Ekonomi 2026.
    Sengaja hanya memeriksa title + rss_snippet (bukan content hasil
    scraping), karena content bisa tercemar tautan "Baca juga: <judul
    lain>" yang membuat artikel tak relevan lolos filter (lihat
    is_relevant_entry di se_news_scraper.py — logic yang sama dipakai
    saat pengambilan berita baru, supaya konsisten)."""
    return is_relevant_entry(title, snippet)


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
        SELECT id, title, rss_snippet
        FROM se_news_articles
        ORDER BY published_date DESC
    """)

    all_articles = cursor.fetchall()
    print(f"  Total artikel di database: {len(all_articles)}")

    # Check relevance
    print("\n[2] Memeriksa relevansi artikel...")
    irrelevant_ids = []
    relevant_count = 0

    for article_id, title, snippet in all_articles:
        if not is_relevant_article(title, snippet):
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
