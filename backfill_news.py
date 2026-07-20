"""
SATRIA SE2026 — Backfill Berita Sensus Ekonomi 2026
Script ini mengambil berita dari berbagai sumber RSS untuk mengisi
data dari 1 Januari 2026 hingga hari ini.

Cara menjalankan:
    .\.venv\Scripts\python.exe backfill_news.py
"""

import os
import sys
import time
import hashlib
import calendar
import re
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlencode, urlparse

import requests
import feedparser
from bs4 import BeautifulSoup

# Tambahkan path project
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from se_news_storage import SeNewsStorage
from se_news_analyzer import SeNewsAnalyzer

WIB = ZoneInfo('Asia/Jakarta')
UTC = ZoneInfo('UTC')

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SATRIA-SE2026'
)
REQUEST_TIMEOUT = 15

# ── Query terms yang lebih luas ──────────────────────────────────────────────
QUERY_TERMS = [
    'Sensus Ekonomi 2026',
    'SE2026 BPS',
    'Sensus Ekonomi BPS 2026',
    '"Sensus Ekonomi" 2026',
    'BPS sensus ekonomi',
    'Badan Pusat Statistik sensus 2026',
    'sensus ekonomi dua ribu dua puluh enam',
    'SE2026',
    'sensus usaha 2026',
    'pendataan ekonomi 2026',
    'sensus ekonomi nasional 2026',
    'BPS SE2026',
    'data ekonomi BPS 2026',
    'petugas sensus ekonomi 2026',
    'formulir sensus ekonomi 2026',
]

# ── Sumber RSS tambahan (bukan Google News) ──────────────────────────────────
DIRECT_RSS_FEEDS = [
    # Kompas
    'https://rss.kompas.com/money/ekonomi',
    'https://rss.kompas.com/money/fiskal',
    # Detik Finance
    'https://finance.detik.com/rss',
    # CNN Indonesia Ekonomi
    'https://www.cnnindonesia.com/ekonomi/rss',
    # CNBC Indonesia
    'https://www.cnbcindonesia.com/rss',
    # Bisnis.com
    'https://rss.bisnis.com/ekonomi',
    # Tempo
    'https://rss.tempo.co/bisnis',
    # Antara
    'https://www.antaranews.com/rss/terkini.xml',
    # Liputan6
    'https://www.liputan6.com/feed/tag/sensus-ekonomi',
    # Tribun
    'https://www.tribunnews.com/bisnis/rss',
]

SE_KEYWORDS = [
    'sensus ekonomi', 'se2026', 'se 2026', 'sensus ekonomi 2026',
    'bps sensus', 'pendataan usaha', 'petugas sensus',
    'formulir se', 'sensus usaha',
]


def url_hash(url):
    return hashlib.sha1(url.encode('utf-8')).hexdigest()


def to_wib(struct_time):
    if not struct_time:
        return datetime.now(WIB).replace(tzinfo=None)
    epoch = calendar.timegm(struct_time)
    dt_utc = datetime.fromtimestamp(epoch, tz=UTC)
    return dt_utc.astimezone(WIB).replace(tzinfo=None)


def clean_snippet(html_summary):
    if not html_summary:
        return ''
    try:
        soup = BeautifulSoup(html_summary, 'lxml')
        text = soup.get_text(separator=' ', strip=True)
    except Exception:
        text = re.sub(r'<[^>]+>', ' ', html_summary)
    return re.sub(r'\s+', ' ', text).strip()


def is_relevant(title, snippet=''):
    """Cek apakah artikel relevan dengan Sensus Ekonomi 2026"""
    text = (title + ' ' + snippet).lower()
    return any(kw in text for kw in SE_KEYWORDS)


def fetch_google_news_rss(query, lang='id', gl='ID'):
    """Ambil dari Google News RSS"""
    params = {'q': query, 'hl': lang, 'gl': gl, 'ceid': f'{gl}:{lang}'}
    url = f"https://news.google.com/rss/search?{urlencode(params)}"

    try:
        resp = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        return feed.entries
    except Exception as e:
        print(f"  [!] RSS fetch gagal untuk '{query}': {e}")
        return []


def fetch_google_news_before_date(query, before_date):
    """Google News RSS dengan filter waktu menggunakan parameter 'before:'"""
    date_str = before_date.strftime('%Y-%m-%d')
    query_with_date = f"{query} before:{date_str}"
    return fetch_google_news_rss(query_with_date)


def fetch_google_news_after_date(query, after_date):
    """Google News RSS dengan filter waktu menggunakan parameter 'after:'"""
    date_str = after_date.strftime('%Y-%m-%d')
    query_with_date = f"{query} after:{date_str}"
    return fetch_google_news_rss(query_with_date)


def fetch_google_news_range(query, after_date, before_date):
    """Google News RSS dengan filter rentang tanggal"""
    after_str = after_date.strftime('%Y-%m-%d')
    before_str = before_date.strftime('%Y-%m-%d')
    query_with_date = f"{query} after:{after_str} before:{before_str}"
    return fetch_google_news_rss(query_with_date)


def fetch_direct_rss(feed_url):
    """Ambil dari RSS feed langsung dan filter yang relevan"""
    try:
        resp = requests.get(feed_url, headers={'User-Agent': USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        return [e for e in feed.entries if is_relevant(
            e.get('title', ''),
            clean_snippet(e.get('summary', ''))
        )]
    except Exception as e:
        print(f"  [!] Direct RSS gagal untuk '{feed_url}': {e}")
        return []


def resolve_google_url(google_link):
    """Resolve URL Google News ke URL artikel asli"""
    host = urlparse(google_link).netloc
    if 'news.google.com' not in host:
        return google_link

    try:
        resp = requests.get(
            google_link,
            headers={'User-Agent': USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        final_host = urlparse(resp.url).netloc
        if 'news.google.com' not in final_host:
            return resp.url
    except Exception:
        pass
    return google_link


def entries_to_rows(entries, source_hint='Google News'):
    """Konversi feedparser entries ke format rows yang bisa disimpan"""
    rows = []
    seen = set()
    for entry in entries:
        link = entry.get('link', '')
        if not link:
            continue

        h = url_hash(link)
        if h in seen:
            continue
        seen.add(h)

        # Ambil source
        source = source_hint
        source_obj = entry.get('source')
        if source_obj:
            source = source_obj.get('title') if hasattr(source_obj, 'get') else str(source_obj)

        pub_date = to_wib(entry.get('published_parsed'))
        title = entry.get('title', '').strip()
        snippet = clean_snippet(entry.get('summary', ''))

        rows.append({
            'title': title,
            'url': link,
            'url_hash': h,
            'source': source,
            'rss_snippet': snippet,
            'query_keyword': 'backfill',
            'published_date': pub_date,
        })
    return rows


def scrape_content(url):
    """Scrape isi artikel. Picks whichever <article> candidate (or the whole
    page as a fallback) yields the most paragraph text — sites with several
    <article> tags (related-post teasers, not just the main story) often
    have the real content in a different one than the first."""
    try:
        resp = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'lxml')

        for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'iframe']):
            tag.decompose()

        def paragraph_text(node):
            text = ' '.join(p.get_text(' ', strip=True) for p in node.find_all('p'))
            return re.sub(r'\s+', ' ', text).strip()

        candidates = soup.find_all('article') or [soup]
        best_text = max((paragraph_text(c) for c in candidates), key=len, default='')

        if len(best_text) < 200:
            whole_page_text = paragraph_text(soup)
            if len(whole_page_text) > len(best_text):
                best_text = whole_page_text

        return best_text if len(best_text) >= 200 else None
    except Exception:
        return None


def main():
    print("=" * 60)
    print("SATRIA SE2026 — Backfill Berita Sensus Ekonomi 2026")
    print("=" * 60)

    storage = SeNewsStorage()
    analyzer = SeNewsAnalyzer()

    if not storage.use_mysql:
        print("[✗] Database tidak tersedia. Hentikan proses.")
        return

    start_date = date(2026, 1, 1)
    today = date.today()
    total_new = 0
    all_rows = []
    seen_hashes = set()

    def add_rows(rows):
        nonlocal total_new
        for r in rows:
            if r['url_hash'] not in seen_hashes:
                seen_hashes.add(r['url_hash'])
                all_rows.append(r)

    print(f"\n[1] Mengambil berita via Google News RSS (query langsung)...")
    for i, query in enumerate(QUERY_TERMS):
        print(f"  Query [{i+1}/{len(QUERY_TERMS)}]: {query}")
        entries = fetch_google_news_rss(query)
        rows = entries_to_rows(entries, 'Google News')
        add_rows(rows)
        print(f"    → {len(rows)} artikel ditemukan")
        time.sleep(1.5)

    print(f"\n[2] Mengambil berita dengan filter tanggal per kuartal...")
    quarters = [
        (date(2026, 1, 1),  date(2026, 3, 31)),
        (date(2026, 4, 1),  date(2026, 6, 30)),
        (date(2026, 7, 1),  today),
    ]

    core_queries = [
        'Sensus Ekonomi 2026',
        'SE2026 BPS',
        '"Sensus Ekonomi" BPS',
        'sensus ekonomi petugas',
        'BPS sensus ekonomi daerah',
    ]

    for q_start, q_end in quarters:
        if q_end > today:
            q_end = today
        label = f"{q_start.strftime('%b')}–{q_end.strftime('%b %Y')}"
        print(f"\n  Kuartal {label}:")
        for query in core_queries:
            entries = fetch_google_news_range(query, q_start, q_end)
            rows = entries_to_rows(entries, 'Google News')
            add_rows(rows)
            print(f"    '{query[:40]}' → {len(rows)} artikel")
            time.sleep(1.5)

    print(f"\n[3] Mengambil dari RSS sumber berita langsung...")
    for feed_url in DIRECT_RSS_FEEDS:
        print(f"  Feed: {feed_url[:60]}")
        entries = fetch_direct_rss(feed_url)
        rows = entries_to_rows(entries, feed_url.split('/')[2])
        add_rows(rows)
        print(f"    → {len(rows)} artikel relevan")
        time.sleep(1)

    print(f"\n[4] Mencari per bulan untuk coverage penuh Jan–Jul 2026...")
    months = []
    cur = start_date
    while cur <= today:
        month_end_day = (date(cur.year, cur.month % 12 + 1, 1) - timedelta(days=1)) if cur.month < 12 else date(cur.year, 12, 31)
        if month_end_day > today:
            month_end_day = today
        months.append((cur, month_end_day))
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)

    for m_start, m_end in months:
        month_label = m_start.strftime('%B %Y')
        print(f"\n  Bulan {month_label}:")
        month_queries = [
            f'Sensus Ekonomi 2026 {m_start.strftime("%B")}',
            f'BPS sensus ekonomi {m_start.strftime("%B %Y")}',
            'Sensus Ekonomi 2026',
        ]
        for query in month_queries:
            entries = fetch_google_news_range(query, m_start, m_end)
            rows = entries_to_rows(entries, 'Google News')
            add_rows(rows)
            if rows:
                print(f"    '{query[:50]}' → {len(rows)} artikel")
            time.sleep(1.2)

    print(f"\n{'='*60}")
    print(f"Total artikel unik ditemukan: {len(all_rows)}")
    print(f"\n[5] Menyimpan ke database...")

    if all_rows:
        new_count = storage.insert_articles_bulk(all_rows)
        total_new += new_count
        print(f"  → {new_count} artikel baru tersimpan")
    else:
        print("  → Tidak ada artikel baru")

    print(f"\n[6] Scraping konten artikel yang pending (maks 200)...")
    pending = storage.get_pending_scrape_articles(limit=200)
    print(f"  → {len(pending)} artikel pending scrape")

    ok = failed = 0
    to_analyze = []
    for i, art in enumerate(pending):
        print(f"  [{i+1}/{len(pending)}] {art['title'][:60]}...")

        resolved_url = resolve_google_url(art['url'])
        content = None

        if resolved_url and 'news.google.com' not in resolved_url:
            content = scrape_content(resolved_url)

        if content:
            storage.update_article_scrape_result(
                art['id'], resolved_url, content, 'scraped', 'success'
            )
            ok += 1
            to_analyze.append({
                'id': art['id'],
                'title': art['title'],
                'source': art['source'],
                'url': art['url'],
                'published_date': art['published_date'],
                'content': content,
            })
            print(f"    ✓ Scraped ({len(content)} chars)")
        else:
            snippet = art.get('rss_snippet', '')
            storage.update_article_scrape_result(
                art['id'], resolved_url, snippet or None,
                'rss_snippet' if snippet else 'none', 'failed'
            )
            if snippet:
                to_analyze.append({
                    'id': art['id'],
                    'title': art['title'],
                    'source': art['source'],
                    'url': art['url'],
                    'published_date': art['published_date'],
                    'content': snippet,
                })
            failed += 1
            print(f"    ✗ Gagal scrape (pakai snippet)")

        time.sleep(0.5)

    print(f"\n  Scrape selesai: {ok} sukses, {failed} gagal")

    print(f"\n[7] Analisis sentimen untuk {len(to_analyze)} artikel...")
    if to_analyze:
        try:
            analyzer.analyze_and_store(storage, to_analyze)
            print(f"  ✓ Analisis sentimen selesai")
        except Exception as e:
            print(f"  ✗ Error analisis sentimen: {e}")

    print(f"\n{'='*60}")
    print(f"BACKFILL SELESAI!")
    print(f"  Total artikel baru tersimpan : {total_new}")
    print(f"  Total artikel scraped OK     : {ok}")
    print(f"  Total artikel scraped gagal  : {failed}")
    print(f"  Total dianalisis sentimen    : {len(to_analyze)}")
    print(f"{'='*60}")

    # Tampilkan statistik per hari (coverage check)
    print(f"\n[8] Mengecek coverage per bulan...")
    for m_start, m_end in months:
        year = m_start.year
        month = m_start.month
        counts = storage.get_daily_counts(year, month)
        days_with_news = len(counts)
        total_in_month = sum(r['count'] for r in counts)
        import calendar as cal
        total_days = cal.monthrange(year, month)[1]
        # Hanya hitung hari yang sudah berlalu
        if m_end >= today:
            total_days = (today - m_start).days + 1
        pct = (days_with_news / max(total_days, 1)) * 100
        print(f"  {m_start.strftime('%B %Y')}: {days_with_news}/{total_days} hari ada berita "
              f"({total_in_month} artikel, {pct:.0f}% coverage)")


if __name__ == '__main__':
    main()
