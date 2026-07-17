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
