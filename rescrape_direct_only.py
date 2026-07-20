"""
SATRIA SE2026 — Scrape full content for articles with a DIRECT (non-Google)
URL only.

Google's news.google.com article-resolution endpoint is currently rate-
limiting this environment's IP persistently (confirmed via repeated manual
tests returning HTTP 429), so retrying Google-sourced articles wastes time
for a near-zero success rate. Articles discovered from direct publisher RSS
feeds (Kompas, Detik, CNN Indonesia, Antara, etc. — see backfill_news.py's
DIRECT_RSS_FEEDS) never touch that endpoint at all, so they can be scraped
right now regardless of the Google-side block.
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from db_config import get_connection
from se_news_storage import SeNewsStorage
from se_news_scraper import scrape_article_content

WORKERS = 6


def fetch_direct_pending(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, title, url
        FROM se_news_articles
        WHERE url NOT LIKE '%news.google.com%'
          AND scrape_status != 'success'
        ORDER BY id
    """)
    return cur.fetchall()


def process_one(article):
    content = scrape_article_content(article['url'])
    if content:
        return article['id'], article['url'], content, 'scraped', 'success'
    return article['id'], article['url'], None, 'none', 'failed'


def main():
    conn = get_connection()
    articles = fetch_direct_pending(conn)
    conn.close()
    print(f"Artikel dengan link langsung (non-Google): {len(articles)}")
    if not articles:
        print("Tidak ada artikel direct-link untuk diproses.")
        return

    storage = SeNewsStorage()
    start = time.time()
    ok = failed = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(process_one, a): a for a in articles}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                article_id, resolved, content, content_source, scrape_status = fut.result()
            except Exception as e:
                a = futures[fut]
                print(f"  [!] error on id={a['id']}: {e}")
                continue

            storage.update_article_scrape_result(article_id, resolved, content, content_source, scrape_status)
            if scrape_status == 'success':
                ok += 1
            else:
                failed += 1

            if i % 20 == 0 or i == len(articles):
                elapsed = time.time() - start
                print(f"  -> {i}/{len(articles)} diproses ({ok} sukses, {failed} gagal, {elapsed:.0f}s)")

    print(f"\nSelesai. Sukses: {ok}, gagal: {failed}")


if __name__ == '__main__':
    sys.exit(main())
