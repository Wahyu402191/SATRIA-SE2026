"""
SATRIA SE2026 — Berita Sensus Ekonomi 2026: Scraper
Badan Pusat Statistik Kabupaten Bangkalan

Discovers news articles about "Sensus Ekonomi 2026" via Google News RSS
(free, no API key), then best-effort scrapes the full article body for
sentiment analysis. Phase 1 (RSS discovery) and phase 2 (content scraping)
are decoupled on purpose: a failure in phase 2 for one article never
blocks phase 1's daily article counting for any other article.
"""

import os
import re
import json
import time
import hashlib
import calendar
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlencode, urlparse

import requests
import feedparser
from bs4 import BeautifulSoup

WIB = ZoneInfo('Asia/Jakarta')
UTC = ZoneInfo('UTC')

GOOGLE_NEWS_RSS_URL = 'https://news.google.com/rss/search'
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SATRIA-SE2026-NewsMonitor'
)
REQUEST_TIMEOUT = 10
MIN_CONTENT_LENGTH = 200


def get_query_terms():
    """Query terms are configurable via .env so coverage can be tuned
    without a code change (a single term is usually too narrow)."""
    raw = os.getenv('SE_NEWS_QUERY_TERMS', 'Sensus Ekonomi 2026,SE2026 BPS,Sensus Ekonomi BPS')
    return [q.strip() for q in raw.split(',') if q.strip()]


def _url_hash(url):
    return hashlib.sha1(url.encode('utf-8')).hexdigest()


def _to_wib(struct_time):
    """Convert a feedparser struct_time (always UTC) to a naive WIB
    datetime, so 'today' in the app matches the user's local calendar day."""
    if not struct_time:
        return datetime.now(WIB).replace(tzinfo=None)
    epoch = calendar.timegm(struct_time)
    dt_utc = datetime.fromtimestamp(epoch, tz=UTC)
    return dt_utc.astimezone(WIB).replace(tzinfo=None)


def _clean_snippet(html_summary):
    """Google News RSS <description> is an HTML blob (an <a> + <font>) —
    strip tags, keep the plain text summary."""
    if not html_summary:
        return ''
    try:
        soup = BeautifulSoup(html_summary, 'lxml')
        text = soup.get_text(separator=' ', strip=True)
    except Exception:
        text = re.sub(r'<[^>]+>', ' ', html_summary)
    text = text.replace('&nbsp;', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def fetch_rss_entries(query, max_results=100):
    """Phase 1 — fetch Google News RSS for one query term.
    Returns raw dicts: title, link, published_date (WIB, naive), source, snippet.
    Never raises — a failed request just yields an empty list.
    """
    params = {'q': query, 'hl': 'id', 'gl': 'ID', 'ceid': 'ID:id'}
    url = f"{GOOGLE_NEWS_RSS_URL}?{urlencode(params)}"

    try:
        resp = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[se_news_scraper] RSS fetch failed for '{query}': {e}")
        return []

    feed = feedparser.parse(resp.content)
    entries = []
    for entry in feed.entries[:max_results]:
        link = entry.get('link', '')
        if not link:
            continue

        source = None
        source_obj = entry.get('source')
        if source_obj:
            source = source_obj.get('title') if hasattr(source_obj, 'get') else str(source_obj)

        entries.append({
            'title': entry.get('title', '').strip(),
            'link': link,
            'published_date': _to_wib(entry.get('published_parsed')),
            'source': source or 'Tidak diketahui',
            'snippet': _clean_snippet(entry.get('summary', '')),
            'query_keyword': query,
        })
    return entries


def fetch_new_articles():
    """Orchestrates fetch_rss_entries() over all configured query terms and
    dedupes within this batch by url_hash. Returns (rows, total_found) where
    rows are ready for storage.insert_articles_bulk(). A failing query term
    is skipped silently — others still contribute.
    """
    seen_hashes = set()
    rows = []
    total_found = 0

    for query in get_query_terms():
        entries = fetch_rss_entries(query)
        total_found += len(entries)
        for e in entries:
            h = _url_hash(e['link'])
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            rows.append({
                'title': e['title'],
                'url': e['link'],
                'url_hash': h,
                'source': e['source'],
                'rss_snippet': e['snippet'],
                'query_keyword': e['query_keyword'],
                'published_date': e['published_date'],
            })
        time.sleep(1)  # be polite between queries

    return rows, total_found


def _decode_google_news_url(google_link, page_html):
    """Google's `/rss/articles/<opaque-id>` links no longer 30x-redirect to
    the publisher (Google resolves them client-side with JS instead). The
    news.google.com article page embeds a signature/timestamp pair that the
    same JS uses to call an internal batchexecute RPC and get the real URL
    back — this replicates that call. Returns None if the page doesn't have
    the expected markup or the RPC fails (e.g. Google changes the format)."""
    m_sig = re.search(r'data-n-a-sg="([^"]+)"', page_html)
    m_ts = re.search(r'data-n-a-ts="([^"]+)"', page_html)
    if not (m_sig and m_ts):
        return None
    signature, timestamp = m_sig.group(1), m_ts.group(1)
    article_id = urlparse(google_link).path.rsplit('/', 1)[-1]

    inner_payload = [
        'garturlreq',
        [['en-ID', 'ID', ['FINANCE_TOP_INDICES', 'WEB_TEST_1_0_0'], None, None, 1, 1,
          'ID:en', None, 180, None, None, None, None, None, 0, None, None,
          [1608992183, 723341000]],
         'en-ID', 'ID', 1, [2, 4, 8], 1, 1, None, 0, 0, None, 0],
        article_id, timestamp, signature,
    ]
    payload = [[['Fbv4je', json.dumps(inner_payload), None, 'generic']]]

    try:
        resp = requests.post(
            'https://news.google.com/_/DotsSplashUi/data/batchexecute',
            data={'f.req': json.dumps(payload)},
            headers={'User-Agent': USER_AGENT,
                     'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.text.split('\n', 1)[1] if resp.text.startswith(")]}'") else resp.text
        outer = json.loads(body)
        inner = json.loads(outer[0][2])
        return inner[1]
    except Exception:
        return None


def resolve_article_url(google_link, description_html=''):
    """Best-effort resolution of the real publisher URL:
    1. If the link's host isn't news.google.com, it's already direct.
    2. Follow HTTP redirects with `requests`; if the final host isn't
       news.google.com, use it (works for the old-style Google News links).
    3. New-style opaque `/rss/articles/...` links stay on news.google.com
       even after following redirects — decode them via the batchexecute
       trick in `_decode_google_news_url`.
    4. Try to pull the first <a href> out of the RSS <description> HTML.
    5. Otherwise give up — caller falls back to the rss_snippet.
    """
    host = urlparse(google_link).netloc
    if 'news.google.com' not in host:
        return google_link

    page_html = None
    try:
        resp = requests.get(google_link, headers={'User-Agent': USER_AGENT},
                            timeout=REQUEST_TIMEOUT, allow_redirects=True)
        final_host = urlparse(resp.url).netloc
        if 'news.google.com' not in final_host:
            return resp.url
        page_html = resp.text
    except requests.RequestException:
        pass

    if page_html:
        decoded = _decode_google_news_url(google_link, page_html)
        if decoded:
            return decoded

    if description_html:
        try:
            soup = BeautifulSoup(description_html, 'lxml')
            a = soup.find('a', href=True)
            if a and 'news.google.com' not in urlparse(a['href']).netloc:
                return a['href']
        except Exception:
            pass

    return None


def scrape_article_content(url):
    """Generic full-article text extraction (requests + BeautifulSoup).
    Pages (especially WordPress sites) often have several <article> tags —
    related-post teasers, not just the main story — so instead of trusting
    the first one, extract paragraph text from every candidate and keep
    whichever yields the most text (the real story is reliably the longest).
    Returns None if the page couldn't be fetched or the best candidate is
    still too short to be a real article body (treated as extraction failure)."""
    try:
        resp = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    try:
        soup = BeautifulSoup(resp.content, 'lxml')
    except Exception:
        return None

    for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'iframe', 'form']):
        tag.decompose()

    def paragraph_text(node):
        text = ' '.join(p.get_text(' ', strip=True) for p in node.find_all('p'))
        return re.sub(r'\s+', ' ', text).strip()

    candidates = soup.find_all('article') or [soup]
    best_text = max((paragraph_text(c) for c in candidates), key=len, default='')

    if len(best_text) < MIN_CONTENT_LENGTH:
        whole_page_text = paragraph_text(soup)
        if len(whole_page_text) > len(best_text):
            best_text = whole_page_text

    if len(best_text) < MIN_CONTENT_LENGTH:
        return None
    return best_text


def enrich_one_article(article_row):
    """Phase 2, single article — never raises. Always returns a result dict
    with resolved_url/content/content_source/scrape_status so one bad
    article never breaks the batch loop."""
    url = article_row['url']
    snippet = article_row.get('rss_snippet') or ''

    resolved = None
    content = None
    try:
        resolved = resolve_article_url(url)
        if resolved:
            content = scrape_article_content(resolved)
    except Exception as e:
        print(f"[se_news_scraper] enrich failed for {url}: {e}")

    if content:
        return {
            'resolved_url': resolved,
            'content': content,
            'content_source': 'scraped',
            'scrape_status': 'success',
        }

    return {
        'resolved_url': resolved,
        'content': snippet or None,
        'content_source': 'rss_snippet' if snippet else 'none',
        'scrape_status': 'failed',
    }
