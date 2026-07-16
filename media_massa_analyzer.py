"""
SATRIA SE2026 — Media Massa Sentiment Analyzer
Badan Pusat Statistik Kabupaten Bangkalan

Sentiment analysis for news articles from various media sources
Uses the same ML models as YouTube analysis (Naive Bayes, SVM, LSTM, IndoBERT)
"""

from sentiment_analyzer import SentimentAnalyzer
import time


class MediaMassaAnalyzer:
    def __init__(self):
        """
        Initialize analyzer using existing SentimentAnalyzer
        """
        self.analyzer = SentimentAnalyzer()
        print("[✓] MediaMassaAnalyzer initialized with 4 ML methods")
    
    def analyze_articles(self, articles, selected_methods):
        """
        Analyze news articles using selected ML methods
        Similar to analyze_multiple_methods but for news articles
        
        Args:
            articles: List of article dicts with 'content' field
            selected_methods: List of method names ['naive_bayes', 'svm', 'lstm', 'indobert']
        
        Returns:
            Dict with analyzed articles, summary, and statistics
        """
        start_time = time.time()
        
        method_map = {
            'naive_bayes': 'Naive Bayes',
            'svm': 'SVM',
            'lstm': 'LSTM',
            'indobert': 'IndoBERT',
        }
        
        sentiment_map = {
            'positif': 'positive',
            'negatif': 'negative',
            'netral': 'neutral',
        }
        
        results = {
            'articles': [],
            'summary': {},
            'preprocessing_examples': [],
        }
        
        # Initialize summary
        for method_key in selected_methods:
            results['summary'][method_map.get(method_key, method_key)] = {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
        
        n = len(articles)
        print(f"[INFO] Analyzing {n} articles with {len(selected_methods)} methods...")
        
        # Step 1: Batch preprocess
        print(f"[PERF] Preprocessing {n} articles...")
        t0 = time.time()
        preprocessed_texts = [
            self.analyzer.preprocessor.preprocess_simple(a['content'])
            for a in articles
        ]
        print(f"[PERF] Preprocessing done in {time.time()-t0:.2f}s")
        
        # Gather 3 detailed preprocessing examples
        for idx in range(min(3, n)):
            _, steps = self.analyzer.preprocessor.preprocess_detailed(articles[idx]['content'])
            results['preprocessing_examples'].append({
                'article_index': idx + 1,
                'title': articles[idx]['title'],
                'steps': steps,
            })
        
        # Step 2: Batch ML inference
        print(f"[PERF] Running batch inference...")
        t1 = time.time()
        batch_results = self.analyzer.ml_analyzer.predict_batch(preprocessed_texts, selected_methods)
        print(f"[PERF] Batch inference done in {time.time()-t1:.2f}s")
        
        # Step 3: Merge results
        for idx, article in enumerate(articles):
            br = batch_results[idx]
            article_result = {
                'id': article.get('id'),
                'title': article['title'],
                'content': article['content'],
                'source': article.get('source', 'Unknown'),
                'url': article.get('url', ''),
                'published_date': article.get('published_date', ''),
            }
            
            # Add sentiment results for each method
            if 'naive_bayes' in selected_methods:
                label = br['naive_bayes_sentiment']
                article_result['naive_bayes_sentiment'] = label
                article_result['naive_bayes_score'] = br['naive_bayes_score']
                key = sentiment_map.get(label.lower(), label.lower())
                results['summary']['Naive Bayes'][key] += 1
            
            if 'svm' in selected_methods:
                label = br['svm_sentiment']
                article_result['svm_sentiment'] = label
                article_result['svm_score'] = br['svm_score']
                key = sentiment_map.get(label.lower(), label.lower())
                results['summary']['SVM'][key] += 1
            
            if 'lstm' in selected_methods:
                label = br['lstm_sentiment']
                article_result['lstm_sentiment'] = label
                article_result['lstm_score'] = br['lstm_score']
                key = sentiment_map.get(label.lower(), label.lower())
                results['summary']['LSTM'][key] += 1
            
            if 'indobert' in selected_methods:
                label = br['indobert_sentiment']
                article_result['indobert_sentiment'] = label
                article_result['indobert_score'] = br['indobert_score']
                key = sentiment_map.get(label.lower(), label.lower())
                results['summary']['IndoBERT'][key] += 1
            
            results['articles'].append(article_result)
        
        print(f"[PERF] Total analyze_articles: {time.time()-start_time:.2f}s for {n} articles")
        
        # Calculate accuracy and confusion matrices if multiple methods
        if len(selected_methods) > 1:
            results['accuracy'] = self._calculate_cross_method_accuracy(
                results['articles'], selected_methods
            )
            results['confusion_matrices'] = self._generate_confusion_matrices(
                results['articles'], selected_methods
            )
        
        return results
    
    def _calculate_cross_method_accuracy(self, analyzed_articles, methods):
        """
        Calculate agreement accuracy between methods
        Uses majority voting as ground truth
        """
        from collections import Counter
        
        accuracy_scores = {}
        all_predictions = {method: [] for method in methods}
        
        for article in analyzed_articles:
            predictions_for_article = []
            
            for method in methods:
                sentiment_key = f"{method}_sentiment"
                
                if sentiment_key in article:
                    sentiment = article[sentiment_key]
                    all_predictions[method].append(sentiment)
                    predictions_for_article.append(sentiment)
            
            # Majority vote as "ground truth"
            if predictions_for_article:
                majority = Counter(predictions_for_article).most_common(1)[0][0]
                
                # Calculate agreement for each method
                for method in methods:
                    sentiment_key = f"{method}_sentiment"
                    if sentiment_key in article:
                        if method not in accuracy_scores:
                            accuracy_scores[method] = {'correct': 0, 'total': 0}
                        
                        accuracy_scores[method]['total'] += 1
                        if article[sentiment_key] == majority:
                            accuracy_scores[method]['correct'] += 1
        
        # Calculate percentage
        result = {}
        for method, scores in accuracy_scores.items():
            if scores['total'] > 0:
                accuracy = (scores['correct'] / scores['total']) * 100
                result[method] = round(accuracy, 2)
            else:
                result[method] = 0.0
        
        return result
    
    def _generate_confusion_matrices(self, analyzed_articles, methods):
        """
        Generate confusion matrix for each method compared to majority vote
        """
        from collections import Counter
        import numpy as np
        
        confusion_matrices = {}
        sentiment_labels = ['Negatif', 'Netral', 'Positif']
        label_to_idx = {label: idx for idx, label in enumerate(sentiment_labels)}
        
        # Get majority votes
        majority_votes = []
        for article in analyzed_articles:
            predictions = []
            for method in methods:
                sentiment_key = f"{method}_sentiment"
                if sentiment_key in article:
                    predictions.append(article[sentiment_key])
            
            if predictions:
                majority = Counter(predictions).most_common(1)[0][0]
                majority_votes.append(majority)
            else:
                majority_votes.append('Netral')
        
        # Build confusion matrix for each method
        for method in methods:
            matrix = np.zeros((3, 3), dtype=int)
            
            for idx, article in enumerate(analyzed_articles):
                sentiment_key = f"{method}_sentiment"
                if sentiment_key in article and idx < len(majority_votes):
                    predicted = article[sentiment_key]
                    actual = majority_votes[idx]
                    
                    if predicted in label_to_idx and actual in label_to_idx:
                        pred_idx = label_to_idx[predicted]
                        actual_idx = label_to_idx[actual]
                        matrix[actual_idx][pred_idx] += 1
            
            confusion_matrices[method] = {
                'matrix': matrix.tolist(),
                'labels': sentiment_labels
            }
        
        return confusion_matrices
    
    def generate_word_trend_weekly(self, articles, month_value):
        """
        Generate word trend analysis per week for articles in a month
        
        Args:
            articles: List of articles with published_date
            month_value: Month string 'YYYY-MM'
        
        Returns:
            Dict with weeks, words, and data for chart
        """
        from collections import Counter, defaultdict
        import re
        from datetime import datetime
        
        # Stopwords
        stopwords = {
            'yang', 'dan', 'di', 'ke', 'dari', 'ini', 'itu', 'ada',
            'juga', 'dengan', 'untuk', 'adalah', 'tidak', 'pada',
            'akan', 'bisa', 'sudah', 'tersebut', 'dapat', 'oleh',
            'dalam', 'telah', 'sebagai', 'lebih', 'saat', 'kata',
            'bahwa', 'atau', 'kami', 'kita', 'mereka', 'dia', 'ia',
            'bps', 'sensus', 'ekonomi', 'data', 'tahun', 'bulan'
        }
        
        weekly = defaultdict(Counter)
        
        for article in articles:
            pub_date_str = article.get('published_date', '')
            if not pub_date_str:
                continue
            
            try:
                pub_date = datetime.fromisoformat(pub_date_str)
                # Get week number (1-4/5)
                week_num = (pub_date.day - 1) // 7 + 1
                week_key = f"Minggu {week_num}"
            except:
                continue
            
            # Process content
            content = str(article.get('content', '')).lower()
            content = re.sub(r'http\S+|www\S+|https\S+', ' ', content)
            content = re.sub(r'@\w+|#\w+', ' ', content)
            content = re.sub(r'\d+', ' ', content)
            content = re.sub(r'[^\w\s]', ' ', content)
            
            words = [w for w in content.split() if len(w) > 3 and w not in stopwords]
            weekly[week_key].update(words)
        
        if not weekly:
            return {'weeks': [], 'words': [], 'data': {}}
        
        # Sort weeks
        weeks = sorted(weekly.keys(), key=lambda x: int(x.split()[1]))
        
        # Top 8 words overall
        overall = Counter()
        for cnt in weekly.values():
            overall.update(cnt)
        top_words = [w for w, _ in overall.most_common(8)]
        
        # Build series data
        data = {}
        for word in top_words:
            data[word] = [weekly[w].get(word, 0) for w in weeks]
        
        return {'weeks': weeks, 'words': top_words, 'data': data}
    
    def generate_wordcloud(self, analyzed_articles):
        """
        Generate dual wordclouds (positive and negative) from analyzed articles
        """
        return self.analyzer.generate_wordcloud(analyzed_articles)
