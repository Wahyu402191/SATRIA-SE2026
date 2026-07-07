"""
ML-based Sentiment Analysis with 4 methods:
1. Naive Bayes
2. Support Vector Machine (SVM)
3. LSTM/BiLSTM (simulated with pre-trained model)
4. IndoBERT (simulated with lexicon-based approach)

Note: Full implementation requires large models and training data.
This is a lightweight version using sklearn and pre-trained approach.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
import pickle
import os

class MLSentimentAnalyzer:
    def __init__(self, positive_words, negative_words, sentiwords, boosterwords=None, emoticons=None, negation_words=None):
        """
        Initialize ML-based sentiment analyzer with enhanced lexicons
        """
        self.positive_words = positive_words
        self.negative_words = negative_words
        self.sentiwords = sentiwords
        self.boosterwords = boosterwords or {}
        self.emoticons = emoticons or {}
        self.negation_words = negation_words or set()
        
        # Initialize vectorizers with better parameters
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=2000,
            ngram_range=(1, 3),  # Unigram, bigram, trigram
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,  # Use logarithmic TF scaling
            use_idf=True
        )
        
        # Initialize models (will be trained on-the-fly with lexicon-based labels)
        self.nb_model = None
        self.svm_model = None
        
        # Training data cache
        self.training_samples = []
        self.training_labels = []
        self._prepare_enhanced_training_data()
        
        print("[INFO] ML Sentiment Analyzer initialized")
    
    def _prepare_enhanced_training_data(self):
        """
        Prepare better training data from lexicons
        Create synthetic training samples with context
        Include all 3 classes: Positive (2), Neutral (1), Negative (0)
        """
        # Positive samples (more diverse)
        pos_words = list(self.positive_words)[:150]
        for word in pos_words:
            # Single word
            self.training_samples.append(word)
            self.training_labels.append(2)  # Positif
            
            # With context
            self.training_samples.append(f"sangat {word}")
            self.training_labels.append(2)
            
            self.training_samples.append(f"{word} sekali")
            self.training_labels.append(2)
        
        # Negative samples (more diverse)
        neg_words = list(self.negative_words)[:150]
        for word in neg_words:
            # Single word
            self.training_samples.append(word)
            self.training_labels.append(0)  # Negatif
            
            # With context
            self.training_samples.append(f"sangat {word}")
            self.training_labels.append(0)
            
            self.training_samples.append(f"{word} sekali")
            self.training_labels.append(0)
        
        # Neutral samples (balanced) - IMPORTANT: Must have neutral class!
        neutral_samples = [
            "biasa saja", "standar", "lumayan", "cukup", "oke", "normal",
            "sedang sedang saja", "tidak apa apa", "begitu begitu saja",
            "ya gitu deh", "hmm", "oh", "begitu", "iya",  "oh begitu",
            "okey", "ya sudah", "gitu", "begitu ya", "oke lah",
            "lumayan lah", "standar aja", "biasa", "cukup lah", "yaudah",
            "sip", "mantap deh", "baiklah", "nah gitu", "oh gitu"
        ]
        # Repeat to balance with pos/neg (we have ~450 pos and ~450 neg, so need ~300 neutral)
        for _ in range(10):  # 30 samples * 10 = 300 neutral samples
            for sample in neutral_samples:
                self.training_samples.append(sample)
                self.training_labels.append(1)  # Netral
        
        print(f"[INFO] Prepared {len(self.training_samples)} training samples (Pos: {self.training_labels.count(2)}, Neg: {self.training_labels.count(0)}, Neutral: {self.training_labels.count(1)})")
    
    def _prepare_training_data(self, texts):
        """
        Generate pseudo training data from lexicon scoring
        This is a workaround for not having labeled dataset
        """
        labels = []
        for text in texts:
            score = self._calculate_lexicon_score(text)
            if score > 0.2:
                labels.append(2)  # Positive
            elif score < -0.2:
                labels.append(0)  # Negative
            else:
                labels.append(1)  # Neutral
        return labels
    
    def _calculate_lexicon_score(self, text):
        """
        Calculate enhanced lexicon-based sentiment score
        Uses all available lexicons including boosters, emoticons, negation
        """
        words = text.lower().split()
        if len(words) == 0:
            return 0.0
        
        total_score = 0
        matched_words = 0
        
        for i, word in enumerate(words):
            # Check for negation in previous 2 words
            negated = False
            if i > 0:
                if words[i-1] in self.negation_words:
                    negated = True
                elif i > 1 and words[i-2] in self.negation_words:
                    negated = True
            
            # Check booster in previous word
            booster = 1.0
            if i > 0 and words[i-1] in self.boosterwords:
                booster = self.boosterwords[words[i-1]]
            
            # Calculate base score
            word_score = 0
            if word in self.sentiwords:
                word_score = self.sentiwords[word]
                matched_words += 1
            elif word in self.positive_words:
                word_score = 3
                matched_words += 1
            elif word in self.negative_words:
                word_score = -3
                matched_words += 1
            elif word in self.emoticons:
                word_score = self.emoticons[word]
                matched_words += 1
            
            # Apply negation (flip the score)
            if negated and word_score != 0:
                word_score = -word_score
            
            # Apply booster
            word_score *= booster
            
            total_score += word_score
        
        if matched_words > 0:
            return total_score / len(words)
        return 0.0
    
    def naive_bayes_analysis(self, text):
        """
        Naive Bayes Classification
        Uses TF-IDF features and Multinomial Naive Bayes
        Auto-trains on first call using enhanced lexicon-based training data
        """
        try:
            # Auto-train on first call if model doesn't exist
            if self.nb_model is None and len(self.training_samples) > 100:
                # Train TF-IDF vectorizer and NB model
                X = self.tfidf_vectorizer.fit_transform(self.training_samples)
                self.nb_model = MultinomialNB(alpha=0.5)  # Lower alpha for less smoothing
                self.nb_model.fit(X, self.training_labels)
                print(f"[INFO] Naive Bayes trained on {len(self.training_samples)} samples")
            
            # Predict
            if self.nb_model is not None:
                X_test = self.tfidf_vectorizer.transform([text])
                pred = self.nb_model.predict(X_test)[0]
                proba = self.nb_model.predict_proba(X_test)[0]
                
                sentiment_map = {0: 'Negatif', 1: 'Netral', 2: 'Positif'}
                score = proba[pred]
                
                # Apply threshold to reduce false classifications
                if pred == 1 and score < 0.6:  # Netral with low confidence
                    # Check lexicon score
                    lex_score = self._calculate_lexicon_score(text)
                    if lex_score > 0.15:
                        return 'Positif', round(float(score), 3)
                    elif lex_score < -0.15:
                        return 'Negatif', round(float(score), 3)
                
                return sentiment_map[pred], round(float(score), 3)
            else:
                # Fallback to lexicon
                score = self._calculate_lexicon_score(text)
                if score > 0.1:
                    return 'Positif', abs(score)
                elif score < -0.1:
                    return 'Negatif', abs(score)
                return 'Netral', 0.0
                
        except Exception as e:
            print(f"[ERROR] Naive Bayes: {e}")
            # Fallback
            score = self._calculate_lexicon_score(text)
            if score > 0.1:
                return 'Positif', abs(score)
            elif score < -0.1:
                return 'Negatif', abs(score)
            return 'Netral', 0.0
    
    def svm_analysis(self, text):
        """
        Support Vector Machine Classification
        Uses TF-IDF features and Linear SVM
        Auto-trains on first call using enhanced lexicon-based training data
        """
        try:
            # Auto-train on first call if model doesn't exist
            if self.svm_model is None and len(self.training_samples) > 100:
                # Train TF-IDF vectorizer and SVM model
                X = self.tfidf_vectorizer.fit_transform(self.training_samples)
                self.svm_model = LinearSVC(
                    C=1.5,  # Higher C for stricter classification
                    max_iter=2000,
                    random_state=42,
                    class_weight='balanced'  # Handle class imbalance
                )
                self.svm_model.fit(X, self.training_labels)
                print(f"[INFO] SVM trained on {len(self.training_samples)} samples")
            
            # Predict
            if self.svm_model is not None:
                X_test = self.tfidf_vectorizer.transform([text])
                pred = self.svm_model.predict(X_test)[0]
                
                # Get decision function for confidence
                decision = self.svm_model.decision_function(X_test)[0]
                
                # Normalize decision to [0, 1] for score
                if isinstance(decision, np.ndarray):
                    score = float(np.max(np.abs(decision)))
                else:
                    score = float(abs(decision))
                score = min(1.0, score / 3.0)  # Better normalization
                
                sentiment_map = {0: 'Negatif', 1: 'Netral', 2: 'Positif'}
                
                # Apply threshold to reduce false classifications
                if pred == 1 and score < 0.5:  # Netral with low confidence
                    # Check lexicon score
                    lex_score = self._calculate_lexicon_score(text)
                    if lex_score > 0.15:
                        return 'Positif', round(score, 3)
                    elif lex_score < -0.15:
                        return 'Negatif', round(score, 3)
                
                return sentiment_map[pred], round(score, 3)
            else:
                # Fallback to lexicon
                score = self._calculate_lexicon_score(text)
                if score > 0.1:
                    return 'Positif', abs(score)
                elif score < -0.1:
                    return 'Negatif', abs(score)
                return 'Netral', 0.0
                
        except Exception as e:
            print(f"[ERROR] SVM: {e}")
            # Fallback
            score = self._calculate_lexicon_score(text)
            if score > 0.1:
                return 'Positif', abs(score)
            elif score < -0.1:
                return 'Negatif', abs(score)
            return 'Netral', 0.0
    
    def lstm_analysis(self, text):
        """
        LSTM/BiLSTM Analysis (Simulated)
        In production, this would use a pre-trained LSTM model
        For now, using enhanced lexicon-based with sequence awareness
        """
        try:
            words = text.lower().split()
            if len(words) == 0:
                return 'Netral', 0.0
            
            # Simulate LSTM sequence processing with context window
            sequence_scores = []
            window_size = 3
            
            for i in range(len(words)):
                # Get context window
                start = max(0, i - window_size)
                end = min(len(words), i + window_size + 1)
                window = words[start:end]
                
                # Calculate score for window
                window_score = 0
                for word in window:
                    if word in self.sentiwords:
                        window_score += self.sentiwords[word]
                    elif word in self.positive_words:
                        window_score += 3
                    elif word in self.negative_words:
                        window_score -= 3
                
                sequence_scores.append(window_score)
            
            # LSTM-like: Use final state (last scores have more weight)
            if sequence_scores:
                # Weighted average: recent scores have more weight
                weights = np.linspace(0.5, 1.0, len(sequence_scores))
                weighted_score = np.average(sequence_scores, weights=weights)
                avg_score = weighted_score / len(words)
                
                if avg_score > 0.15:
                    return 'Positif', round(abs(avg_score), 3)
                elif avg_score < -0.15:
                    return 'Negatif', round(abs(avg_score), 3)
                return 'Netral', 0.0
            
            return 'Netral', 0.0
            
        except Exception as e:
            print(f"[ERROR] LSTM: {e}")
            return 'Netral', 0.0
    
    def indobert_analysis(self, text):
        """
        IndoBERT Analysis (Simulated)
        In production, this would use IndoBERT transformer model
        For now, using advanced lexicon with contextual understanding
        """
        try:
            words = text.lower().split()
            if len(words) == 0:
                return 'Netral', 0.0
            
            # Simulate BERT's bidirectional context understanding
            # Consider word position, negation, and intensifiers
            
            total_score = 0
            intensifiers = {'sangat': 1.5, 'amat': 1.5, 'sekali': 1.3, 'banget': 1.3}
            negations = {'tidak', 'bukan', 'jangan', 'gak', 'ga', 'nggak', 'ngga'}
            
            i = 0
            while i < len(words):
                word = words[i]
                multiplier = 1.0
                is_negated = False
                
                # Check for intensifier before
                if i > 0 and words[i-1] in intensifiers:
                    multiplier = intensifiers[words[i-1]]
                
                # Check for negation before
                if i > 0 and words[i-1] in negations:
                    is_negated = True
                
                # Get word sentiment
                word_score = 0
                if word in self.sentiwords:
                    word_score = self.sentiwords[word]
                elif word in self.positive_words:
                    word_score = 3
                elif word in self.negative_words:
                    word_score = -3
                
                # Apply negation (flip sentiment)
                if is_negated:
                    word_score = -word_score
                
                # Apply intensifier
                word_score *= multiplier
                
                total_score += word_score
                i += 1
            
            # BERT-like normalization with attention mechanism simulation
            avg_score = total_score / len(words)
            
            # More sensitive thresholds for BERT
            if avg_score > 0.1:
                return 'Positif', round(abs(avg_score), 3)
            elif avg_score < -0.1:
                return 'Negatif', round(abs(avg_score), 3)
            return 'Netral', 0.0
            
        except Exception as e:
            print(f"[ERROR] IndoBERT: {e}")
            return 'Netral', 0.0