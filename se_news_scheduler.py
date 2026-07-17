"""
SATRIA SE2026 — Berita Sensus Ekonomi 2026: Background Scheduler
Badan Pusat Statistik Kabupaten Bangkalan

Runs the fetch→scrape→analyze pipeline automatically every few hours
(APScheduler), and exposes run_fetch_job() so the manual "Refresh Sekarang"
button can trigger the exact same pipeline on demand.
"""

import os
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import se_news_scraper as scraper


def run_fetch_job(storage, analyzer, trigger_type='scheduler'):
    """Fetch new articles from RSS, scrape their content best-effort, then
    auto-analyze sentiment for whatever just got scraped. Never raises —
    failures are recorded in se_news_fetch_log instead."""
    interval_hours = int(os.getenv('SE_NEWS_FETCH_INTERVAL_HOURS', 3))

    if trigger_type == 'scheduler' and storage.recent_fetch_already_ran(interval_hours * 60):
        print("[se_news_scheduler] Skipping — a successful run already happened recently.")
        return {'skipped': True}

    log_id = storage.log_fetch_start(trigger_type)
    try:
        rows, total_found = scraper.fetch_new_articles()
        new_count = storage.insert_articles_bulk(rows)

        pending = storage.get_pending_scrape_articles(limit=100)
        ok = failed = 0
        to_analyze = []

        for art in pending:
            result = scraper.enrich_one_article(art)
            storage.update_article_scrape_result(
                art['id'], result['resolved_url'], result['content'],
                result['content_source'], result['scrape_status']
            )
            if result['scrape_status'] == 'success':
                ok += 1
            else:
                failed += 1
            if result['content']:
                to_analyze.append({
                    'id': art['id'], 'title': art['title'], 'source': art['source'],
                    'url': art['url'], 'published_date': art['published_date'],
                    'content': result['content'],
                })

        if to_analyze:
            analyzer.analyze_and_store(storage, to_analyze)

        storage.log_fetch_complete(log_id, articles_found=total_found, articles_new=new_count,
                                    articles_scraped_ok=ok, articles_scraped_failed=failed,
                                    status='success')
        print(f"[se_news_scheduler] Run complete: found={total_found} new={new_count} "
              f"scraped_ok={ok} scraped_failed={failed} analyzed={len(to_analyze)}")
        return {'found': total_found, 'new': new_count, 'ok': ok, 'failed': failed}

    except Exception as e:
        print(f"[se_news_scheduler] Run failed: {e}")
        storage.log_fetch_complete(log_id, status='failed', error_message=str(e))
        return {'error': str(e)}


def init_scheduler(storage, analyzer):
    interval_hours = int(os.getenv('SE_NEWS_FETCH_INTERVAL_HOURS', 3))

    scheduler = BackgroundScheduler(timezone='Asia/Jakarta')
    scheduler.add_job(
        lambda: run_fetch_job(storage, analyzer, 'scheduler'),
        trigger=IntervalTrigger(hours=interval_hours),
        id='se_news_fetch',
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    print(f"[✓] Berita SE2026 scheduler started (every {interval_hours}h)")
    return scheduler
