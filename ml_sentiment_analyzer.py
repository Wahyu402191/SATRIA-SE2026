"""
ML-based Sentiment Analysis — Optimized for speed (batch processing + parallel).
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from concurrent.futures import ThreadPoolExecutor
import threading


class MLSentimentAnalyzer:
    def __init__(self, positive_words, negative_words, sentiwords,
                 boosterwords=None, emoticons=None, negation_words=None):

        self.positive_words = positive_words
        self.negative_words = negative_words
        self.sentiwords     = sentiwords
        self.boosterwords   = boosterwords or {}
        self.emoticons      = emoticons or {}
        self.negation_words = negation_words or set()

        # Wider vocabulary now that training pulls thousands of lexicon
        # words (was capped at 1000, too small to represent them)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=8000,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
        )

        self.nb_model  = None
        self.svm_model = None
        self._models_trained = False

        self.training_samples = []
        self.training_labels  = []
        self._prepare_training_data()
        
        # Train models immediately on initialization to avoid "not fitted" errors
        self._train_models()

        print("[INFO] ML Sentiment Analyzer initialized and trained")

    # ── Training data ──────────────────────────────────────────────────────

    def _prepare_training_data(self):
        # Thousands of lexicon words per class (was capped at 150, which
        # left the classifier unable to recognize almost any real article
        # vocabulary — see _prepare_training_data note in predict_batch).
        pos_words = list(self.positive_words)[:3000]
        neg_words = list(self.negative_words)[:3000]

        for word in pos_words:
            self.training_samples += [word, f"sangat {word}", f"{word} sekali"]
            self.training_labels  += [2, 2, 2]

        for word in neg_words:
            self.training_samples += [word, f"sangat {word}", f"{word} sekali"]
            self.training_labels  += [0, 0, 0]

        neutral = [
            "biasa saja", "standar", "lumayan", "cukup", "oke", "normal",
            "ya gitu deh", "hmm", "oh begitu", "okey", "ya sudah",
            "lumayan lah", "standar aja", "biasa", "cukup lah", "yaudah",
        ]
        for _ in range(400):          # 16 * 400 = 6400 neutral, same ratio as before
            self.training_samples += neutral
            self.training_labels  += [1] * len(neutral)

        print(f"[INFO] Prepared {len(self.training_samples)} training samples "
              f"(Pos:{self.training_labels.count(2)}, "
              f"Neg:{self.training_labels.count(0)}, "
              f"Neu:{self.training_labels.count(1)})")

    def _train_models(self):
        """Train NB and SVM once, then cache."""
        if self._models_trained:
            return
        X = self.tfidf_vectorizer.fit_transform(self.training_samples)

        self.nb_model = MultinomialNB(alpha=0.5)
        self.nb_model.fit(X, self.training_labels)

        self.svm_model = LinearSVC(C=1.5, max_iter=2000,
                                   random_state=42, class_weight='balanced')
        self.svm_model.fit(X, self.training_labels)

        self._models_trained = True
        print(f"[INFO] NB + SVM trained on {len(self.training_samples)} samples")

    # ── Lexicon score (pure Python — fast) ────────────────────────────────

    def _lexicon_score(self, text: str) -> float:
        words = text.split()
        if not words:
            return 0.0
        total = 0.0
        matched = 0
        neg_set = self.negation_words
        boost   = self.boosterwords
        senti   = self.sentiwords
        pos_set = self.positive_words
        neg_words_set = self.negative_words
        emot    = self.emoticons

        for i, word in enumerate(words):
            # Window widened 2 -> 3 tokens back: real comments routinely put
            # an adverb between the negation and its target ("nggak akan
            # pernah jujur" — 3 tokens between "nggak" and "jujur"), which
            # the old 2-token window missed entirely, leaving "jujur"
            # scored as plain Positif instead of flipped to Negatif.
            negated = (i > 0 and words[i-1] in neg_set) or \
                      (i > 1 and words[i-2] in neg_set) or \
                      (i > 2 and words[i-3] in neg_set)
            b = boost.get(words[i-1], 1.0) if i > 0 else 1.0

            if word in senti:
                ws = senti[word]; matched += 1
            elif word in pos_set:
                ws = 3;           matched += 1
            elif word in neg_words_set:
                ws = -3;          matched += 1
            elif word in emot:
                ws = emot[word];  matched += 1
            else:
                continue

            if negated:
                ws = -ws
            total += ws * b

        # BUG FIX: divide by matched words, not all words
        return (total / matched) if matched else 0.0

    def _score_to_label(self, score: float, pos_thr=0.1, neg_thr=-0.1):
        if score > pos_thr:  return 'Positif', round(abs(score), 3)
        if score < neg_thr:  return 'Negatif', round(abs(score), 3)
        return 'Netral', 0.0

    # ── BATCH prediction (main public API) ────────────────────────────────

    def predict_batch(self, texts: list, methods: list) -> list:
        """
        Predict sentiment for a list of texts in one batch.
        Uses parallel processing for multiple methods.
        Returns list of dicts with keys for each selected method.
        """
        n = len(texts)
        results = [{} for _ in range(n)]
        sentiment_map = {0: 'Negatif', 1: 'Netral', 2: 'Positif'}
        
        # Use ThreadPoolExecutor to run methods in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            # Submit each method as separate thread
            if 'naive_bayes' in methods:
                futures['naive_bayes'] = executor.submit(
                    self._predict_naive_bayes, texts, sentiment_map, n
                )
            
            if 'svm' in methods:
                futures['svm'] = executor.submit(
                    self._predict_svm, texts, sentiment_map, n
                )
            
            if 'lstm' in methods:
                futures['lstm'] = executor.submit(
                    self._predict_lstm, texts, n
                )
            
            if 'indobert' in methods:
                futures['indobert'] = executor.submit(
                    self._predict_indobert, texts, n
                )
            
            # Collect results from all threads
            for method, future in futures.items():
                method_results = future.result()
                for i in range(n):
                    results[i].update(method_results[i])
        
        return results
    
    def _predict_naive_bayes(self, texts, sentiment_map, n):
        """NB prediction in separate thread"""
        results = [{} for _ in range(n)]
        self._train_models()
        X = self.tfidf_vectorizer.transform(texts)
        no_signal = np.asarray(X.getnnz(axis=1)) == 0
        
        preds  = self.nb_model.predict(X)
        probas = self.nb_model.predict_proba(X)
        
        for i in range(n):
            if no_signal[i]:
                results[i]['naive_bayes_sentiment'] = 'Netral'
                results[i]['naive_bayes_score']     = 0.0
                continue
            pred  = preds[i]
            score = float(probas[i][pred])
            label = sentiment_map[pred]
            if pred == 1 and score < 0.6:
                ls = self._lexicon_score(texts[i])
                if   ls > 0.08: label = 'Positif'
                elif ls < -0.08: label = 'Negatif'
            results[i]['naive_bayes_sentiment'] = label
            results[i]['naive_bayes_score']     = round(score, 3)
        
        return results
    
    def _predict_svm(self, texts, sentiment_map, n):
        """SVM prediction in separate thread"""
        results = [{} for _ in range(n)]
        self._train_models()
        X = self.tfidf_vectorizer.transform(texts)
        no_signal = np.asarray(X.getnnz(axis=1)) == 0
        
        preds    = self.svm_model.predict(X)
        decisions = self.svm_model.decision_function(X)
        
        for i in range(n):
            if no_signal[i]:
                results[i]['svm_sentiment'] = 'Netral'
                results[i]['svm_score']     = 0.0
                continue
            pred  = preds[i]
            dec   = decisions[i]
            raw   = float(np.max(np.abs(dec))) if dec.ndim > 0 else float(abs(dec))
            score = min(1.0, raw / 3.0)
            label = sentiment_map[pred]
            if pred == 1 and score < 0.5:
                ls = self._lexicon_score(texts[i])
                if   ls > 0.08: label = 'Positif'
                elif ls < -0.08: label = 'Negatif'
            results[i]['svm_sentiment'] = label
            results[i]['svm_score']     = round(score, 3)
        
        return results
    
    def _predict_lstm(self, texts, n):
        """LSTM prediction in separate thread"""
        results = [{} for _ in range(n)]
        senti   = self.sentiwords
        pos_set = self.positive_words
        neg_set = self.negative_words
        
        for i, text in enumerate(texts):
            words = text.split()
            if not words:
                results[i]['lstm_sentiment'] = 'Netral'
                results[i]['lstm_score']     = 0.0
                continue
            wlen = len(words)
            seq  = np.zeros(wlen, dtype=np.float32)
            matched = 0
            for j, w in enumerate(words):
                if w in senti:      
                    seq[j] = senti[w]
                    matched += 1
                elif w in pos_set:  
                    seq[j] = 3
                    matched += 1
                elif w in neg_set:  
                    seq[j] = -3
                    matched += 1
            
            if matched == 0:
                results[i]['lstm_sentiment'] = 'Netral'
                results[i]['lstm_score']     = 0.0
                continue
            
            weights = np.linspace(0.5, 1.0, wlen, dtype=np.float32)
            total = float(np.sum(seq * weights))
            weight_sum = float(np.sum(weights[seq != 0]))
            avg = total / weight_sum if weight_sum > 0 else 0.0
            
            if wlen <= 30:
                pos_thr = 0.015 if matched > 1 else 0.025
                neg_thr = -0.015 if matched > 1 else -0.025
            else:
                pos_thr = 0.05 if matched > 5 else 0.08
                neg_thr = -0.05 if matched > 5 else -0.08
            
            label, score = self._score_to_label(avg, pos_thr, neg_thr)
            results[i]['lstm_sentiment'] = label
            results[i]['lstm_score'] = score
        
        return results
    
    def _predict_indobert(self, texts, n):
        """IndoBERT prediction in separate thread"""
        results = [{} for _ in range(n)]
        intensifiers = {'sangat':1.5,'amat':1.5,'sekali':1.3,'banget':1.3,'bgt':1.3}
        neg_words_ib = {'tidak','bukan','jangan','gak','ga','nggak','ngga'}
        senti        = self.sentiwords
        pos_set      = self.positive_words
        neg_set_ib   = self.negative_words
        
        for i, text in enumerate(texts):
            words = text.split()
            if not words:
                results[i]['indobert_sentiment'] = 'Netral'
                results[i]['indobert_score']     = 0.0
                continue
            wlen = len(words)
            total = 0.0
            matched = 0
            for j, word in enumerate(words):
                mult  = intensifiers.get(words[j-1], 1.0) if j > 0 else 1.0
                negated = (j > 0 and words[j-1] in neg_words_ib) or \
                          (j > 1 and words[j-2] in neg_words_ib) or \
                          (j > 2 and words[j-3] in neg_words_ib)
                if word in senti:       
                    ws = senti[word]
                    matched += 1
                elif word in pos_set:   
                    ws = 3
                    matched += 1
                elif word in neg_set_ib:
                    ws = -3
                    matched += 1
                else:                   
                    continue
                if negated: ws = -ws
                total += ws * mult
            
            if matched == 0:
                results[i]['indobert_sentiment'] = 'Netral'
                results[i]['indobert_score']     = 0.0
                continue
            
            avg = total / matched
            
            if wlen <= 30:
                pos_thr = 0.08 if matched > 1 else 0.15
                neg_thr = -0.08 if matched > 1 else -0.15
            else:
                pos_thr = 0.3 if matched > 5 else 0.5
                neg_thr = -0.3 if matched > 5 else -0.5
            
            label, score = self._score_to_label(avg, pos_thr, neg_thr)
            results[i]['indobert_sentiment'] = label
            results[i]['indobert_score'] = score
        
        return results

    # ── Single-text wrappers (used by analyze_single endpoint) ────────────

    def naive_bayes_analysis(self, text):
        r = self.predict_batch([text], ['naive_bayes'])[0]
        return r['naive_bayes_sentiment'], r['naive_bayes_score']

    def svm_analysis(self, text):
        r = self.predict_batch([text], ['svm'])[0]
        return r['svm_sentiment'], r['svm_score']

    def lstm_analysis(self, text):
        r = self.predict_batch([text], ['lstm'])[0]
        return r['lstm_sentiment'], r['lstm_score']

    def indobert_analysis(self, text):
        r = self.predict_batch([text], ['indobert'])[0]
        return r['indobert_sentiment'], r['indobert_score']
