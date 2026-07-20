"""
SATRIA SE2026 — Backfill Berita Sensus Ekonomi 2026 (FOCUSED VERSION)
Script khusus untuk mengisi berita dari Januari-Juli 2026
dengan filter ketat: HANYA berita tentang Sensus Ekonomi 2026
"""

import os
import sys
import time
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlencode

import requests
import feedparser
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Import modul app
from db_config import get_connection

load_dotenv()
WIB = ZoneInfo('Asia/Jakarta')

# Filter keywords yang HARUS ada di judul atau konten
REQUIRED_KEYWORDS = [
    'sensus ekonomi 2026',
    'sensus ekonomi',
    'se2026',
    'se 2026',
]

# Blacklist keywords - berita yang mengandung ini akan diabaikan
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
    'musik',
    'film',
    'artis',
    'selebriti',
]

def is_relevant_article(title, snippet):
    """Cek apakah artikel relevan dengan Sensus Ekonomi 2026"""
    text = (title + ' ' + snippet).lower()
    
    # Cek blacklist dulu
    for blackword in BLACKLIST_KEYWORDS:
        if blackword in text:
            return False
    
    # Cek apakah ada keyword yang required
    for keyword in REQUIRED_KEYWORDS:
        if keyword in text:
            return True
    
    return False


def fetch_google_news_by_date(query, start_date, end_date):
    """
    Fetch berita dari Google News RSS dengan filter tanggal
    """
    # Format query dengan date range
    date_str = f"{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}"
    full_query = f"{query} after:{start_date.strftime('%Y-%m-%d')} before:{end_date.strftime('%Y-%m-%d')}"
    
    params = {
        'q': full_query,
        'hl': 'id',
        'gl': 'ID',
        'ceid': 'ID:id'
    }
    
    url = f"https://news.google.com/rss/search?{urlencode(params)}"
    
    try:
        resp = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ✗ RSS fetch failed: {e}")
        return []
    
    feed = feedparser.parse(resp.content)
    articles = []
    
    for entry in feed.entries[:50]:  # Max 50 per query
        title = entry.get('title', '').strip()
        link = entry.get('link', '')
        summary = entry.get('summary', '')
        
        if not link or not title:
            continue
        
        # Clean snippet
        try:
            soup = BeautifulSoup(summary, 'lxml')
            snippet = soup.get_text(separator=' ', strip=True)
        except:
            snippet = summary
        
        # Filter relevance
        if not is_relevant_article(title, snippet):
            continue
        
        # Parse published date
        pub_parsed = entry.get('published_parsed')
        if pub_parsed:
            import calendar
            epoch = calendar.timegm(pub_parsed)
            from datetime import timezone
            pub_date = datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone(WIB).replace(tzinfo=None)
        else:
            pub_date = datetime.now(WIB).replace(tzinfo=None)
        
        # Get source
        source = 'Tidak diketahui'
        source_obj = entry.get('source')
        if source_obj:
            source = source_obj.get('title') if hasattr(source_obj, 'get') else str(source_obj)
        
        articles.append({
            'title': title,
            'url': link,
            'url_hash': hashlib.sha1(link.encode('utf-8')).hexdigest(),
            'source': source,
            'rss_snippet': snippet,
            'published_date': pub_date,
            'query_keyword': query,
        })
    
    return articles


def backfill_month(year, month, conn):
    """Backfill berita untuk satu bulan"""
    import calendar
    
    month_name = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ][month - 1]
    
    print(f"\n{'='*60}")
    print(f"📅 Backfill {month_name} {year}")
    print('='*60)
    
    # Tentukan range tanggal
    _, last_day = calendar.monthrange(year, month)
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    # Cek tanggal hari ini
    today = datetime.now(WIB).replace(tzinfo=None)
    if end_date > today:
        end_date = today
    
    print(f"Periode: {start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}")
    
    # Query terms yang lebih spesifik
    queries = [
        '"Sensus Ekonomi 2026"',
        'SE2026 BPS',
        'Sensus Ekonomi BPS 2026',
        'pendataan usaha BPS 2026',
        'canangkan sensus ekonomi',
    ]
    
    all_articles = []
    seen_hashes = set()
    
    # Cek artikel yang sudah ada di database untuk bulan ini
    cursor = conn.cursor()
    cursor.execute("""
        SELECT url_hash FROM se_news_articles 
        WHERE DATE_FORMAT(published_date, '%%Y-%%m') = %s
    """, (f"{year:04d}-{month:02d}",))
    
    existing_hashes = {row[0] for row in cursor.fetchall()}
    print(f"Artikel existing di database: {len(existing_hashes)}")
    
    # Fetch dari berbagai query
    for idx, query in enumerate(queries, 1):
        print(f"\n[{idx}/{len(queries)}] Query: {query}")
        articles = fetch_google_news_by_date(query, start_date, end_date)
        print(f"  → Found {len(articles)} artikel")
        
        new_count = 0
        for article in articles:
            h = article['url_hash']
            if h not in seen_hashes and h not in existing_hashes:
                seen_hashes.add(h)
                all_articles.append(article)
                new_count += 1
        
        print(f"  → {new_count} artikel baru (unique)")
        time.sleep(2)  # Rate limiting
    
    print(f"\n📊 Total artikel baru untuk {month_name}: {len(all_articles)}")
    
    if not all_articles:
        print("  ℹ️  Tidak ada artikel baru")
        return 0
    
    # Insert ke database
    print(f"\n[1] Menyimpan {len(all_articles)} artikel ke database...")
    cursor = conn.cursor()
    
    insert_count = 0
    for article in all_articles:
        try:
            cursor.execute("""
                INSERT INTO se_news_articles
                (title, url, url_hash, source, rss_snippet, published_date, query_keyword,
                 resolved_url, content, content_source, scrape_status, discovered_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                article['title'],
                article['url'],
                article['url_hash'],
                article['source'],
                article['rss_snippet'],
                article['published_date'],
                article['query_keyword'],
                None,  # resolved_url
                article['rss_snippet'],  # gunakan snippet sebagai content
                'rss_snippet',
                'pending',
                datetime.now(WIB).replace(tzinfo=None)
            ))
            insert_count += 1
        except Exception as e:
            if 'Duplicate' not in str(e):
                print(f"  ✗ Error insert: {e}")
    
    conn.commit()
    print(f"  ✓ Tersimpan: {insert_count} artikel")
    
    # Analisis sentimen akan dilakukan oleh scheduler otomatis
    # Untuk sekarang, cukup tandai artikel sebagai pending
    
    return insert_count


def main():
    print("="*60)
    print("🎯 BACKFILL BERITA SENSUS EKONOMI 2026 - FOCUSED VERSION")
    print("="*60)
    print("Filter: HANYA berita tentang Sensus Ekonomi 2026")
    print("Periode: Januari - Juli 2026")
    print("="*60)
    
    conn = get_connection()
    
    # Backfill dari Januari sampai Juli 2026
    total_new = 0
    
    months_to_fill = [
        (2026, 1),   # Januari
        (2026, 2),   # Februari
        (2026, 3),   # Maret
        (2026, 4),   # April
        (2026, 5),   # Mei
        (2026, 6),   # Juni
        (2026, 7),   # Juli (sampai hari ini)
    ]
    
    for year, month in months_to_fill:
        count = backfill_month(year, month, conn)
        total_new += count
        time.sleep(3)  # Jeda antar bulan
    
    # Summary
    print("\n" + "="*60)
    print("📊 BACKFILL SELESAI!")
    print("="*60)
    print(f"Total artikel baru ditambahkan: {total_new}")
    
    # Cek coverage per bulan
    cursor = conn.cursor()
    print("\n📅 Coverage per bulan:")
    for year, month in months_to_fill:
        import calendar
        _, last_day = calendar.monthrange(year, month)
        
        # Hitung hari yang ada berita
        cursor.execute("""
            SELECT COUNT(DISTINCT DATE(published_date)) as days_with_news,
                   COUNT(*) as total_articles
            FROM se_news_articles
            WHERE DATE_FORMAT(published_date, '%%Y-%%m') = %s
        """, (f"{year:04d}-{month:02d}",))
        
        row = cursor.fetchone()
        days_with_news = row[0]
        total_articles = row[1]
        
        # Adjust untuk bulan berjalan
        today = datetime.now(WIB).replace(tzinfo=None)
        if year == today.year and month == today.month:
            last_day = today.day
        
        coverage_pct = (days_with_news / last_day * 100) if last_day > 0 else 0
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
        print(f"  {month_names[month-1]} {year}: {total_articles:3d} artikel, "
              f"{days_with_news}/{last_day} hari ({coverage_pct:.0f}%)")
    
    conn.close()
    print("\n✅ Proses selesai!")


if __name__ == '__main__':
    main()
