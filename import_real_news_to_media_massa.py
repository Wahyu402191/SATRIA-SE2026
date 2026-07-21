"""
Replace the Media Massa dashboard's dummy dataset (news_articles) with real,
full-length articles already scraped by the Berita SE2026 module
(se_news_articles) — same underlying data, just reused so Media Massa shows
real journalism instead of templated dummy text.

Only rows with content_source='scraped' (i.e. successfully scraped full
article body, not the short RSS-snippet fallback) and published in 2026 are
copied — this matches the average length the user asked for and keeps
Media Massa's existing "Januari-Desember 2026" scope intact. A handful of
stray older-dated Google News results (2016-2025) that matched the search
keywords by coincidence are intentionally excluded.
"""
from db_config import get_connection, execute_many


def clear_old_data(conn):
    print("[i] Menghapus data dummy lama (news_articles cascades ke news_analysis_results)...")
    cur = conn.cursor()
    cur.execute("DELETE FROM news_articles")
    cur.execute("DELETE FROM news_analysis_sessions")
    conn.commit()
    cur.close()
    print("[i] Data lama sudah dibersihkan.")


def fetch_real_articles(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT title, content, url, source, published_date
        FROM se_news_articles
        WHERE content_source = 'scraped' AND YEAR(published_date) = 2026
        ORDER BY published_date ASC
    """)
    return cur.fetchall()


def main():
    conn = get_connection()
    articles = fetch_real_articles(conn)
    print(f"Artikel asli (full-text, 2026) tersedia: {len(articles)}")

    clear_old_data(conn)

    sources = {a['source'] or 'Tidak diketahui' for a in articles}
    execute_many("INSERT IGNORE INTO news_sources (source_name) VALUES (%s)",
                 [(s,) for s in sources])
    print(f"[i] {len(sources)} sumber media dicatat.")

    rows = [(
        a['title'][:1000],
        a['content'],
        (a['url'] or '')[:1000],
        a['source'] or 'Tidak diketahui',
        a['published_date'],
        a['published_date'].month,
        a['published_date'].year,
    ) for a in articles]

    # Inserted in small batches — a single executemany() over all ~1,100
    # rows (some articles up to 18KB of content) compiles into one giant
    # multi-row INSERT that exceeds MySQL's max_allowed_packet and aborts
    # the whole call with nothing committed.
    BATCH = 40
    inserted = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        execute_many("""
            INSERT INTO news_articles (title, content, url, source, published_date, month, year, imported_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, batch)
        inserted += len(batch)
        print(f"  -> {inserted}/{len(rows)} artikel diimport...")

    print(f"[DONE] {inserted} artikel asli berhasil diimport ke news_articles.")

    conn.close()


if __name__ == '__main__':
    main()
