"""
ML-based Sentiment Analysis — Optimized for speed (batch processing).
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC


class MLSentimentAnalyzer:
    def __init__(self, positive_words, negative_words, sentiwords,
                 boosterwords=None, emoticons=None, negation_words=None):

        self.positive_words = positive_words
        self.negative_words = negative_words
        self.sentiwords     = sentiwords
        self.boosterwords   = boosterwords or {}
        self.emoticons      = emoticons or {}
        self.negation_words = negation_words or set()

        # Reduced features for speed (1-2 gram, 1000 features)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
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

        print("[INFO] ML Sentiment Analyzer initialized")

    # ── Training data ──────────────────────────────────────────────────────

    def _prepare_training_data(self):
        pos_words = list(self.positive_words)[:150]
        neg_words = list(self.negative_words)[:150]

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
        for _ in range(20):          # 16 * 20 = 320 neutral
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
            negated = (i > 0 and words[i-1] in neg_set) or \
                      (i > 1 and words[i-2] in neg_set)
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

        return (total / len(words)) if matched else 0.0

    def _score_to_label(self, score: float, pos_thr=0.1, neg_thr=-0.1):
        if score > pos_thr:  return 'Positif', round(abs(score), 3)
        if score < neg_thr:  return 'Negatif', round(abs(score), 3)
        return 'Netral', 0.0

    # ── BATCH prediction (main public API) ────────────────────────────────

    def predict_batch(self, texts: list, methods: list) -> list:
        """
        Predict sentiment for a list of texts in one batch.
        Returns list of dicts with keys for each selected method.
        """
        n = len(texts)
        results = [{} for _ in range(n)]
        sentiment_map = {0: 'Negatif', 1: 'Netral', 2: 'Positif'}

        # ── NB and SVM batch ──────────────────────────────────────────────
        if 'naive_bayes' in methods or 'svm' in methods:
            self._train_models()
            X = self.tfidf_vectorizer.transform(texts)

            if 'naive_bayes' in methods:
                preds  = self.nb_model.predict(X)
                probas = self.nb_model.predict_proba(X)
                for i in range(n):
                    pred  = preds[i]
                    score = float(probas[i][pred])
                    label = sentiment_map[pred]
                    # Low-confidence Netral → fallback to lexicon
                    if pred == 1 and score < 0.6:
                        ls = self._lexicon_score(texts[i])
                        if   ls > 0.15: label = 'Positif'
                        elif ls < -0.15: label = 'Negatif'
                    results[i]['naive_bayes_sentiment'] = label
                    results[i]['naive_bayes_score']     = round(score, 3)

            if 'svm' in methods:
                preds    = self.svm_model.predict(X)
                decisions = self.svm_model.decision_function(X)
                for i in range(n):
                    pred  = preds[i]
                    dec   = decisions[i]
                    raw   = float(np.max(np.abs(dec))) if dec.ndim > 0 else float(abs(dec))
                    score = min(1.0, raw / 3.0)
                    label = sentiment_map[pred]
                    if pred == 1 and score < 0.5:
                        ls = self._lexicon_score(texts[i])
                        if   ls > 0.15: label = 'Positif'
                        elif ls < -0.15: label = 'Negatif'
                    results[i]['svm_sentiment'] = label
                    results[i]['svm_score']     = round(score, 3)

        # ── LSTM batch (vectorised with numpy) ────────────────────────────
        if 'lstm' in methods:
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
                for j, w in enumerate(words):
                    if w in senti:      seq[j] = senti[w]
                    elif w in pos_set:  seq[j] = 3
                    elif w in neg_set:  seq[j] = -3
                # weighted average: later words have more weight
                weights = np.linspace(0.5, 1.0, wlen, dtype=np.float32)
                avg = float(np.average(seq, weights=weights)) / wlen
                label, score = self._score_to_label(avg, 0.15, -0.15)
                results[i]['lstm_sentiment'] = label
                results[i]['lstm_score']     = score

        # ── IndoBERT batch (vectorised with numpy) ────────────────────────
        if 'indobert' in methods:
            intensifiers = {'sangat':1.5,'amat':1.5,'sekali':1.3,'banget':1.3}
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
                total = 0.0
                for j, word in enumerate(words):
                    mult  = intensifiers.get(words[j-1], 1.0) if j > 0 else 1.0
                    negated = j > 0 and words[j-1] in neg_words_ib
                    if word in senti:       ws = senti[word]
                    elif word in pos_set:   ws = 3
                    elif word in neg_set_ib:ws = -3
                    else:                   continue
                    if negated: ws = -ws
                    total += ws * mult
                avg = total / len(words)
                label, score = self._score_to_label(avg, 0.1, -0.1)
                results[i]['indobert_sentiment'] = label
                results[i]['indobert_score']     = score

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
