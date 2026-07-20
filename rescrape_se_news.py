"""
SATRIA SE2026 — Re-scrape full content for every se_news_articles row.

One-off maintenance script: se_news_scraper.py had two bugs that made
content scraping fail 100% of the time —
  1. `lxml` was in requirements.txt but never actually installed, so every
     BeautifulSoup(..., 'lxml') call raised and was swallowed.
  2. resolve_article_url() only followed HTTP redirects, but Google News'
     current-style /rss/articles/<opaque-id> links don't redirect — Google
     resolves them client-side with JS. resolve_article_url() now decodes
     them via the same internal batchexecute RPC the page's own JS calls.
  3. scrape_article_content() trusted soup.find('article') blindly, which
     on WordPress sites often grabs a related-post teaser instead of the
     real story. It now scores every <article> candidate by paragraph
     text length and keeps the longest.

This re-attempts every article regardless of prior scrape_status (both
'pending' and previously-'failed' rows), using a thread pool since the work
is network-bound (resolve + fetch, two requests per article, many
different domains).
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from db_config import get_connection
from se_news_storage import SeNewsStorage
from se_news_scraper import resolve_article_url, scrape_article_content

WORKERS = 6


def fetch_all(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, title, url, rss_snippet
        FROM se_news_articles
        ORDER BY id
    """)
    return cur.fetchall()


def process_one(article):
    """Google's article-resolution endpoint throttles intermittently, not
    permanently — a request that 400s now can succeed a few seconds later.
    Retry a couple of times with backoff before giving up on an article."""
    resolved = None
    content = None
    for attempt in range(3):
        if attempt:
            time.sleep(3 * attempt)
        resolved = resolve_article_url(article['url'], article.get('rss_snippet') or '')
        if resolved:
            content = scrape_article_content(resolved)
            if content:
                break

    if content:
        return article['id'], resolved, content, 'scraped', 'success'
    snippet = article.get('rss_snippet') or ''
    return article['id'], resolved, (snippet or None), ('rss_snippet' if snippet else 'none'), 'failed'


def main():
    conn = get_connection()
    articles = fetch_all(conn)
    conn.close()
    print(f"Total artikel: {len(articles)}")

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

            if i % 50 == 0 or i == len(articles):
                elapsed = time.time() - start
                print(f"  → {i}/{len(articles)} diproses ({ok} sukses, {failed} gagal, {elapsed:.0f}s)")

    print(f"\nSelesai. Sukses scrape penuh: {ok}, gagal (pakai snippet/none): {failed}")


if __name__ == '__main__':
    sys.exit(main())
