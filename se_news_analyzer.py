"""
SATRIA SE2026 — Berita Sensus Ekonomi 2026: Sentiment Analyzer
Badan Pusat Statistik Kabupaten Bangkalan

Sentiment analysis for auto-discovered news articles. Uses the same 4 ML
methods as the YouTube/Media Massa dashboards (Naive Bayes, SVM, LSTM,
IndoBERT). Each method classifies one article independently at any time —
no batching/training on real data is required — so this is used both to
auto-analyze articles right after scraping, and to re-run/filter results
on demand from the Analisis Sentimen page.
"""

import re
import time
from collections import Counter
import numpy as np

from sentiment_analyzer import SentimentAnalyzer

_METHOD_NAMES = {
    'naive_bayes': 'Naive Bayes',
    'svm': 'SVM',
    'lstm': 'LSTM',
    'indobert': 'IndoBERT',
}

_SENTIMENT_KEY = {
    'positif': 'positive',
    'negatif': 'negative',
    'netral': 'neutral',
}

# Split on '.', '!', '?' followed by whitespace + an uppercase letter/digit/
# opening quote — a reasonable approximation of "next sentence starts here"
# without a full NLP sentence tokenizer.
_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"“])')
_MIN_SENTENCE_CHARS = 15


class SeNewsAnalyzer:
    def __init__(self):
        self.analyzer = SentimentAnalyzer()
        print("[✓] SeNewsAnalyzer initialized with 4 ML methods")

    def analyze_batch(self, articles, methods):
        """Analyze a list of article dicts (must have 'content'; 'id'/
        'title'/'source'/'url'/'published_date' are carried through if
        present). One preprocess pass + one predict_batch call, matching
        the efficient pattern used elsewhere in this repo."""
        start = time.time()

        results = {'articles': [], 'summary': {}, 'preprocessing_examples': []}
        for method in methods:
            results['summary'][_METHOD_NAMES.get(method, method)] = {
                'positive': 0, 'negative': 0, 'neutral': 0
            }

        n = len(articles)
        preprocessed = [self.analyzer.preprocessor.preprocess_simple(a.get('content', '') or '')
                        for a in articles]

        for idx in range(min(3, n)):
            _, steps = self.analyzer.preprocessor.preprocess_detailed(articles[idx].get('content', '') or '')
            results['preprocessing_examples'].append({
                'article_index': idx + 1,
                'title': articles[idx].get('title', ''),
                'steps': steps,
            })

        batch_results = self.analyzer.ml_analyzer.predict_batch(preprocessed, methods)

        for idx, article in enumerate(articles):
            br = batch_results[idx]
            row = {
                'id': article.get('id'),
                'title': article.get('title', ''),
                'source': article.get('source', 'Tidak diketahui'),
                'url': article.get('url', ''),
                'published_date': str(article.get('published_date', '')),
            }
            method_results = {}
            for method in methods:
                label = br[f'{method}_sentiment']
                score = br[f'{method}_score']
                row[f'{method}_sentiment'] = label
                row[f'{method}_score'] = score
                method_results[method] = {'sentiment': label, 'score': score}

                key = _SENTIMENT_KEY.get(label.lower(), label.lower())
                results['summary'][_METHOD_NAMES.get(method, method)][key] += 1

            row['_method_results'] = method_results
            results['articles'].append(row)

        print(f"[PERF] se_news analyze_batch: {n} articles, {len(methods)} methods, {time.time()-start:.2f}s")

        if len(methods) > 1:
            results['accuracy'] = self._calculate_cross_method_accuracy(results['articles'], methods)
            results['confusion_matrices'] = self._generate_confusion_matrices(results['articles'], methods)

        results['keywords'] = self._extract_top_keywords(results['articles'], preprocessed, methods)
        results['source_breakdown'] = self._calculate_source_breakdown(results['articles'], methods)
        results['confidence'] = self._calculate_avg_confidence(results['articles'], methods)
        results['controversial_articles'], results['extreme_articles'] = \
            self._analyze_disagreement(results['articles'], methods)

        return results

    def analyze_and_store(self, storage, articles, methods=None):
        """Run analyze_batch over `articles` (dicts with at least id+content)
        and persist each article's sentiment via storage.save_sentiment_results.
        Used both by the scheduler (auto-analyze right after scraping) and
        by the Analisis Sentimen page's manual 're-run' action."""
        methods = methods or ['naive_bayes', 'svm', 'lstm', 'indobert']
        if not articles:
            return {'analyzed': 0}

        results = self.analyze_batch(articles, methods)
        for row in results['articles']:
            if row.get('id'):
                storage.save_sentiment_results(row['id'], row['_method_results'])

        return {'analyzed': len(results['articles']), 'summary': results['summary']}

    def generate_wordcloud(self, analyzed_articles):
        return self.analyzer.generate_wordcloud(analyzed_articles)

    def explain_sentiment(self, content):
        """Sentence-level breakdown shown in the article detail view: split
        the article into sentences, score each one against the sentiment
        lexicon individually, and let whichever side (Positif vs Negatif)
        has more sentences decide the reported label — mirrors how a
        reader would actually justify "why is this Positif/Negatif" instead
        of a single opaque score for the whole article. Returns None when
        there's no content to break down (e.g. scraping never got past the
        RSS snippet)."""
        content = (content or '').strip()
        if not content:
            return None

        raw_sentences = _SENTENCE_SPLIT_RE.split(content)
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) >= _MIN_SENTENCE_CHARS]
        if not sentences:
            return None

        scored = []
        for sentence in sentences:
            cleaned = self.analyzer.preprocessor.preprocess_simple(sentence)
            score = self.analyzer.ml_analyzer._lexicon_score(cleaned)
            if score > 0.1:
                label = 'Positif'
            elif score < -0.1:
                label = 'Negatif'
            else:
                label = 'Netral'
            scored.append({'text': sentence, 'label': label, 'score': round(float(score), 3)})

        positive = [s for s in scored if s['label'] == 'Positif']
        negative = [s for s in scored if s['label'] == 'Negatif']
        neutral = [s for s in scored if s['label'] == 'Netral']
        total = len(scored)

        def pct(n):
            return round(n / total * 100, 1) if total else 0.0

        if len(positive) > len(negative):
            dominant = 'Positif'
        elif len(negative) > len(positive):
            dominant = 'Negatif'
        elif positive:  # equal counts, both non-zero
            dominant = 'Seimbang'
        else:
            dominant = 'Netral'

        return {
            'total_sentences': total,
            'positive_sentences': positive,
            'negative_sentences': negative,
            'positive_count': len(positive),
            'negative_count': len(negative),
            'neutral_count': len(neutral),
            'positive_pct': pct(len(positive)),
            'negative_pct': pct(len(negative)),
            'neutral_pct': pct(len(neutral)),
            'dominant': dominant,
        }

    # ── Copied from media_massa_analyzer.py (repo convention: duplicate
    #    small per-sub-app logic rather than share a cross-app module) ─────

    def _calculate_cross_method_accuracy(self, analyzed_articles, methods):
        accuracy_scores = {}

        for article in analyzed_articles:
            predictions_for_article = []
            for method in methods:
                key = f"{method}_sentiment"
                if key in article:
                    predictions_for_article.append(article[key])

            if predictions_for_article:
                majority = Counter(predictions_for_article).most_common(1)[0][0]
                for method in methods:
                    key = f"{method}_sentiment"
                    if key in article:
                        if method not in accuracy_scores:
                            accuracy_scores[method] = {'correct': 0, 'total': 0}
                        accuracy_scores[method]['total'] += 1
                        if article[key] == majority:
                            accuracy_scores[method]['correct'] += 1

        result = {}
        for method, scores in accuracy_scores.items():
            result[method] = round((scores['correct'] / scores['total']) * 100, 2) if scores['total'] > 0 else 0.0
        return result

    def _generate_confusion_matrices(self, analyzed_articles, methods):
        confusion_matrices = {}
        sentiment_labels = ['Negatif', 'Netral', 'Positif']
        label_to_idx = {label: idx for idx, label in enumerate(sentiment_labels)}

        majority_votes = []
        for article in analyzed_articles:
            predictions = [article[f"{m}_sentiment"] for m in methods if f"{m}_sentiment" in article]
            majority_votes.append(Counter(predictions).most_common(1)[0][0] if predictions else 'Netral')

        for method in methods:
            matrix = np.zeros((3, 3), dtype=int)
            for idx, article in enumerate(analyzed_articles):
                key = f"{method}_sentiment"
                if key in article and idx < len(majority_votes):
                    predicted = article[key]
                    actual = majority_votes[idx]
                    if predicted in label_to_idx and actual in label_to_idx:
                        matrix[label_to_idx[actual]][label_to_idx[predicted]] += 1
            confusion_matrices[method] = {'matrix': matrix.tolist(), 'labels': sentiment_labels}

        return confusion_matrices

    def _majority_vote(self, article, methods):
        predictions = [article[f'{m}_sentiment'] for m in methods if f'{m}_sentiment' in article]
        return Counter(predictions).most_common(1)[0][0] if predictions else 'Netral'

    def _extract_top_keywords(self, articles, preprocessed, methods, top_n=18):
        """Kata paling sering muncul di berita yang mayoritas metode labeli
        Positif/Negatif — dipakai buat tag cloud di halaman Analisis
        Sentimen. Reuse `preprocessed` (teks sudah bersih dari stopword)
        yang sudah dihitung sekali di awal analyze_batch, bukan proses ulang."""
        counters = {'Positif': Counter(), 'Negatif': Counter()}
        for article, text in zip(articles, preprocessed):
            label = self._majority_vote(article, methods)
            if label in counters:
                counters[label].update(text.split())

        def top_list(counter):
            return [{'word': w, 'count': c} for w, c in counter.most_common(top_n) if c >= 2]

        return {
            'positive': top_list(counters['Positif']),
            'negative': top_list(counters['Negatif']),
        }

    def _calculate_source_breakdown(self, articles, methods, top_n=12):
        """Sebaran sentimen (majority vote) per sumber media, dibatasi ke
        top_n sumber dengan berita terbanyak — dipakai buat bubble chart
        perbandingan sumber di halaman Analisis Sentimen."""
        by_source = {}
        for article in articles:
            source = article.get('source') or 'Tidak diketahui'
            label = self._majority_vote(article, methods)
            bucket = by_source.setdefault(source, {'positive': 0, 'negative': 0, 'neutral': 0})
            bucket[_SENTIMENT_KEY.get(label.lower(), 'neutral')] += 1

        rows = []
        for source, counts in by_source.items():
            total = counts['positive'] + counts['negative'] + counts['neutral']
            if total == 0:
                continue
            dominant_key = max(counts, key=counts.get)
            rows.append({
                'source': source,
                'total': total,
                'positive_pct': round(counts['positive'] / total * 100, 1),
                'negative_pct': round(counts['negative'] / total * 100, 1),
                'neutral_pct': round(counts['neutral'] / total * 100, 1),
                # Label Indonesia ('Positif'/'Negatif'/'Netral') supaya konsisten
                # dengan label yang dipakai di seluruh UI, bukan key internal.
                'dominant': {'positive': 'Positif', 'negative': 'Negatif', 'neutral': 'Netral'}[dominant_key],
            })

        rows.sort(key=lambda r: r['total'], reverse=True)
        return rows[:top_n]

    def _calculate_avg_confidence(self, articles, methods):
        """Rata-rata confidence score per metode, jadi salah satu sumbu
        radar chart perbandingan metode. NB/SVM score itu probabilitas asli
        (0-1), tapi LSTM/IndoBERT scorenya rata-rata bobot leksikon yang tidak
        dibatasi — bisa >1 untuk teks yang kata sentimennya kuat/padat. Clamp
        ke 1.0 dulu sebelum dikalikan 100 supaya confidence-nya tidak pernah
        "lebih dari 100%" yang membingungkan di chart."""
        result = {}
        for method in methods:
            scores = [min(abs(a[f'{method}_score']), 1.0) for a in articles if f'{method}_score' in a]
            result[_METHOD_NAMES.get(method, method)] = round(sum(scores) / len(scores) * 100, 1) if scores else 0.0
        return result

    def _analyze_disagreement(self, articles, methods, top_n=8):
        """Dua sudut pandang yang gampang dipahami tanpa perlu ngerti detail
        4 metode ML-nya:
        - Kontroversial: artikel yang labelnya paling banyak beda-beda antar
          metode (suara mayoritas paling "tipis") — kandidat bagus buat
          ditinjau manual.
        - Ekstrem: artikel Positif/Negatif dengan confidence rata-rata
          tertinggi di antara metode yang sepakat dengan suara mayoritas —
          "yang paling meyakinkan" dari masing-masing sisi."""
        controversial = []
        extreme_positive = None
        extreme_negative = None

        for article in articles:
            preds = [(m, article[f'{m}_sentiment'], article[f'{m}_score'])
                     for m in methods if f'{m}_sentiment' in article]
            if not preds:
                continue

            label_counts = Counter(p[1] for p in preds)
            majority_label, majority_count = label_counts.most_common(1)[0]
            total = len(preds)

            base = {
                'id': article.get('id'),
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'url': article.get('url', ''),
                'published_date': article.get('published_date', ''),
            }

            controversy = round((1 - majority_count / total) * 100, 1)
            if controversy > 0:
                controversial.append({**base, 'controversy': controversy, 'breakdown': dict(label_counts)})

            if majority_label in ('Positif', 'Negatif'):
                agreeing = [min(abs(p[2]), 1.0) for p in preds if p[1] == majority_label]
                candidate = {
                    **base,
                    'confidence': round((sum(agreeing) / len(agreeing)) * 100, 1) if agreeing else 0.0,
                    'agree_count': majority_count,
                    'total_methods': total,
                }
                if majority_label == 'Positif':
                    if extreme_positive is None or candidate['confidence'] > extreme_positive['confidence']:
                        extreme_positive = candidate
                else:
                    if extreme_negative is None or candidate['confidence'] > extreme_negative['confidence']:
                        extreme_negative = candidate

        controversial.sort(key=lambda r: r['controversy'], reverse=True)
        return controversial[:top_n], {'positive': extreme_positive, 'negative': extreme_negative}
