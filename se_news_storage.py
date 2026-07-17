"""
SATRIA SE2026 — Berita Sensus Ekonomi 2026: Storage Layer (MySQL)
Badan Pusat Statistik Kabupaten Bangkalan

Storage handler for auto-discovered news articles (se_news_articles,
se_news_sentiment, se_news_fetch_log — see database.sql).
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from db_config import execute_query, execute_many, get_connection

WIB = ZoneInfo('Asia/Jakarta')

_METHOD_ALIAS = {
    'naive_bayes': 'nb',
    'svm': 'svm',
    'lstm': 'lstm',
    'indobert': 'ib',
}

_ARTICLE_SELECT = """
    SELECT
        a.id, a.title, a.url, a.resolved_url, a.source, a.rss_snippet,
        a.content, a.content_source, a.scrape_status, a.query_keyword,
        a.published_date, a.published_day, a.discovered_at,
        nb.sentiment  AS naive_bayes_sentiment,  nb.confidence_score  AS naive_bayes_score,
        svm.sentiment AS svm_sentiment,           svm.confidence_score AS svm_score,
        lstm.sentiment AS lstm_sentiment,         lstm.confidence_score AS lstm_score,
        ib.sentiment  AS indobert_sentiment,      ib.confidence_score  AS indobert_score
    FROM se_news_articles a
    LEFT JOIN se_news_sentiment nb   ON nb.article_id = a.id   AND nb.method_name = 'naive_bayes'
    LEFT JOIN se_news_sentiment svm  ON svm.article_id = a.id  AND svm.method_name = 'svm'
    LEFT JOIN se_news_sentiment lstm ON lstm.article_id = a.id AND lstm.method_name = 'lstm'
    LEFT JOIN se_news_sentiment ib   ON ib.article_id = a.id   AND ib.method_name = 'indobert'
"""


def _now_wib():
    return datetime.now(WIB).replace(tzinfo=None)


class SeNewsStorage:
    def __init__(self):
        self.use_mysql = self._check_tables()
        if self.use_mysql:
            print("[✓] SeNewsStorage initialized with MySQL backend")
        else:
            print("[!] Warning: se_news_* tables missing. Berita SE2026 features disabled "
                  "until you run database.sql (see the se_news_articles / se_news_sentiment / "
                  "se_news_fetch_log tables).")

    def _check_tables(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'se_news_articles'")
            found = cursor.fetchone() is not None
            cursor.close()
            conn.close()
            return found
        except Exception as e:
            print(f"[!] SeNewsStorage table check failed: {e}")
            return False

    # ── Article ingestion ────────────────────────────────────────────────

    def insert_articles_bulk(self, rows):
        """INSERT IGNORE keyed on url_hash. Returns count of genuinely new
        rows (duplicates are silently ignored, not counted)."""
        if not self.use_mysql or not rows:
            return 0

        query = """
            INSERT IGNORE INTO se_news_articles
                (title, url, url_hash, source, rss_snippet, query_keyword, published_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        data = [(
            r['title'][:1000], r['url'][:1000], r['url_hash'], (r.get('source') or '')[:255],
            r.get('rss_snippet'), r.get('query_keyword'), r['published_date'],
        ) for r in rows]

        return execute_many(query, data)

    def get_pending_scrape_articles(self, limit=50):
        if not self.use_mysql:
            return []
        query = """
            SELECT id, url, rss_snippet, title, source, published_date FROM se_news_articles
            WHERE scrape_status = 'pending'
            ORDER BY discovered_at ASC
            LIMIT %s
        """
        return execute_query(query, (limit,), fetch=True)

    def update_article_scrape_result(self, article_id, resolved_url, content, content_source, scrape_status):
        if not self.use_mysql:
            return
        query = """
            UPDATE se_news_articles
            SET resolved_url = %s, content = %s, content_source = %s,
                scrape_status = %s, scrape_attempted_at = NOW()
            WHERE id = %s
        """
        execute_query(query, (resolved_url, content, content_source, scrape_status, article_id))

    # ── Sentiment ─────────────────────────────────────────────────────────

    def save_sentiment_results(self, article_id, method_results):
        """method_results: {'naive_bayes': {'sentiment': 'Positif', 'score': 0.87}, ...}"""
        if not self.use_mysql or not method_results:
            return
        query = """
            INSERT INTO se_news_sentiment (article_id, method_name, sentiment, confidence_score, analyzed_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                sentiment = VALUES(sentiment),
                confidence_score = VALUES(confidence_score),
                analyzed_at = NOW()
        """
        data = [(article_id, method, res['sentiment'], float(res.get('score', 0.0)))
                for method, res in method_results.items()]
        execute_many(query, data)

    # ── Reads ─────────────────────────────────────────────────────────────

    def get_articles(self, date=None, date_from=None, date_to=None, q=None,
                      source=None, sentiment=None, method='naive_bayes',
                      limit=50, offset=0):
        if not self.use_mysql:
            return []

        where = []
        params = []

        if date:
            where.append("a.published_day = %s")
            params.append(date)
        if date_from:
            where.append("a.published_day >= %s")
            params.append(date_from)
        if date_to:
            where.append("a.published_day <= %s")
            params.append(date_to)
        if q:
            where.append("(a.title LIKE %s OR a.content LIKE %s)")
            like = f"%{q}%"
            params.extend([like, like])
        if source:
            where.append("a.source = %s")
            params.append(source)
        if sentiment:
            alias = _METHOD_ALIAS.get(method, 'nb')
            where.append(f"{alias}.sentiment = %s")
            params.append(sentiment)

        query = _ARTICLE_SELECT
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY a.published_date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        return execute_query(query, tuple(params), fetch=True)

    def get_article_by_id(self, article_id):
        if not self.use_mysql:
            return None
        query = _ARTICLE_SELECT + " WHERE a.id = %s"
        result = execute_query(query, (article_id,), fetch=True)
        return result[0] if result else None

    def get_daily_counts(self, year, month):
        if not self.use_mysql:
            return []
        query = """
            SELECT published_day, COUNT(*) as count
            FROM se_news_articles
            WHERE YEAR(published_day) = %s AND MONTH(published_day) = %s
            GROUP BY published_day
            ORDER BY published_day ASC
        """
        return execute_query(query, (year, month), fetch=True)

    def get_calendar_counts(self, year):
        if not self.use_mysql:
            return []
        query = """
            SELECT published_day, COUNT(*) as count
            FROM se_news_articles
            WHERE YEAR(published_day) = %s
            GROUP BY published_day
            ORDER BY published_day ASC
        """
        return execute_query(query, (year,), fetch=True)

    def get_source_breakdown(self, date_from=None, date_to=None, limit=12):
        if not self.use_mysql:
            return []
        where = []
        params = []
        if date_from:
            where.append("published_day >= %s")
            params.append(date_from)
        if date_to:
            where.append("published_day <= %s")
            params.append(date_to)

        query = "SELECT source, COUNT(*) as count FROM se_news_articles"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " GROUP BY source ORDER BY count DESC LIMIT %s"
        params.append(limit)
        return execute_query(query, tuple(params), fetch=True)

    def get_sentiment_trend(self, date_from, date_to, method='naive_bayes'):
        if not self.use_mysql:
            return []
        query = """
            SELECT a.published_day, s.sentiment, COUNT(*) as count
            FROM se_news_articles a
            JOIN se_news_sentiment s ON s.article_id = a.id AND s.method_name = %s
            WHERE a.published_day BETWEEN %s AND %s
            GROUP BY a.published_day, s.sentiment
            ORDER BY a.published_day ASC
        """
        return execute_query(query, (method, date_from, date_to), fetch=True)

    def get_available_sources(self):
        if not self.use_mysql:
            return []
        result = execute_query(
            "SELECT DISTINCT source FROM se_news_articles WHERE source IS NOT NULL ORDER BY source",
            fetch=True
        )
        return [r['source'] for r in result] if result else []

    def get_statistics(self):
        empty = {
            'total_articles': 0, 'today_count': 0, 'month_count': 0,
            'total_sources': 0, 'total_analyzed': 0,
        }
        if not self.use_mysql:
            return empty

        try:
            now = _now_wib()
            today_str = now.strftime('%Y-%m-%d')

            total = execute_query("SELECT COUNT(*) as c FROM se_news_articles", fetch=True)
            today = execute_query(
                "SELECT COUNT(*) as c FROM se_news_articles WHERE published_day = %s",
                (today_str,), fetch=True
            )
            month = execute_query(
                "SELECT COUNT(*) as c FROM se_news_articles WHERE YEAR(published_day)=%s AND MONTH(published_day)=%s",
                (now.year, now.month), fetch=True
            )
            sources = execute_query(
                "SELECT COUNT(DISTINCT source) as c FROM se_news_articles", fetch=True
            )
            analyzed = execute_query(
                "SELECT COUNT(DISTINCT article_id) as c FROM se_news_sentiment", fetch=True
            )

            return {
                'total_articles': total[0]['c'] if total else 0,
                'today_count': today[0]['c'] if today else 0,
                'month_count': month[0]['c'] if month else 0,
                'total_sources': sources[0]['c'] if sources else 0,
                'total_analyzed': analyzed[0]['c'] if analyzed else 0,
            }
        except Exception as e:
            print(f"[✗] Error getting se_news statistics: {e}")
            return empty

    # ── Fetch log / scheduler guard ──────────────────────────────────────

    def log_fetch_start(self, trigger_type='scheduler'):
        if not self.use_mysql:
            return None
        return execute_query(
            "INSERT INTO se_news_fetch_log (trigger_type, status, started_at) VALUES (%s, 'running', NOW())",
            (trigger_type,)
        )

    def log_fetch_complete(self, log_id, articles_found=0, articles_new=0,
                            articles_scraped_ok=0, articles_scraped_failed=0,
                            status='success', error_message=None):
        if not self.use_mysql or not log_id:
            return
        query = """
            UPDATE se_news_fetch_log
            SET status = %s, completed_at = NOW(), articles_found = %s, articles_new = %s,
                articles_scraped_ok = %s, articles_scraped_failed = %s, error_message = %s
            WHERE id = %s
        """
        execute_query(query, (status, articles_found, articles_new,
                               articles_scraped_ok, articles_scraped_failed,
                               error_message, log_id))

    def get_latest_fetch_log(self):
        if not self.use_mysql:
            return None
        result = execute_query(
            "SELECT * FROM se_news_fetch_log ORDER BY started_at DESC LIMIT 1", fetch=True
        )
        return result[0] if result else None

    def recent_fetch_already_ran(self, interval_minutes, buffer_minutes=5):
        """Cross-process/cross-worker guard: skip a scheduled run if a
        successful fetch already completed recently. Only 'success' rows
        count, so a stranded 'running' row (killed process) never blocks
        future runs."""
        if not self.use_mysql:
            return False
        threshold = max(interval_minutes - buffer_minutes, 1)
        result = execute_query(
            """SELECT id FROM se_news_fetch_log
               WHERE status = 'success' AND completed_at >= (NOW() - INTERVAL %s MINUTE)
               ORDER BY completed_at DESC LIMIT 1""",
            (threshold,), fetch=True
        )
        return bool(result)
