"""
SATRIA SE2026 — Re-run sentiment analysis on ALL se_news_articles rows.

One-off maintenance script: after fixing the NB/SVM "no-signal defaults to
Negatif" tie-break bug and widening the lexicon vocabulary used to train
those models (ml_sentiment_analyzer.py), old rows in se_news_sentiment still
hold labels computed with the buggy code. This re-scores every article
(content, or '' if none was ever scraped) and upserts the results so the
whole table reflects the fix.
"""

import sys
from db_config import get_connection
from se_news_storage import SeNewsStorage
from se_news_analyzer import SeNewsAnalyzer

BATCH_SIZE = 300


def fetch_all_articles(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, title, source, url, published_date, content
        FROM se_news_articles
        ORDER BY id
    """)
    return cur.fetchall()


def main():
    conn = get_connection()
    articles = fetch_all_articles(conn)
    conn.close()
    print(f"Total artikel: {len(articles)}")

    storage = SeNewsStorage()
    analyzer = SeNewsAnalyzer()

    methods = ['naive_bayes', 'svm', 'lstm', 'indobert']
    done = 0
    for start in range(0, len(articles), BATCH_SIZE):
        batch = articles[start:start + BATCH_SIZE]
        for a in batch:
            a['content'] = a.get('content') or ''
        result = analyzer.analyze_and_store(storage, batch, methods=methods)
        done += result['analyzed']
        print(f"  → {done}/{len(articles)} dianalisis ulang")

    print("Selesai re-analisis semua artikel.")


if __name__ == '__main__':
    sys.exit(main())
