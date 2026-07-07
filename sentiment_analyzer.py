import nltk
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from wordcloud import WordCloud
import re
import string
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from ml_sentiment_analyzer import MLSentimentAnalyzer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class TextPreprocessor:
    """
    Class untuk preprocessing text dengan detail steps
    """
    def __init__(self):
        self.stemmer_factory = StemmerFactory()
        self.stemmer = self.stemmer_factory.create_stemmer()
        
        self.stopword_factory = StopWordRemoverFactory()
        self.stopword_remover = self.stopword_factory.create_stop_word_remover()
        
        # Normalization dictionary (slang words)
        self.normalization_dict = {
            'gak': 'tidak', 'ga': 'tidak', 'gk': 'tidak',
            'ngga': 'tidak', 'nggak': 'tidak',
            'udah': 'sudah', 'udh': 'sudah',
            'bgt': 'banget', 'bgt': 'banget',
            'bgus': 'bagus', 'bgs': 'bagus',
            'tp': 'tapi', 'tpi': 'tapi',
            'yg': 'yang', 'sy': 'saya',
            'dr': 'dari', 'dri': 'dari',
            'jd': 'jadi', 'jdi': 'jadi',
            'krn': 'karena', 'krna': 'karena',
            'dgn': 'dengan', 'sm': 'sama',
            'emg': 'emang', 'emng': 'emang',
            'bkn': 'bukan', 'ad': 'ada',
        }
        
        # Spelling correction dictionary (common typos)
        self.spelling_dict = {
            'dngn': 'dengan', 'mnurut': 'menurut', 'mnrt': 'menurut',
            'mngkin': 'mungkin', 'mgkn': 'mungkin',
            'sngat': 'sangat', 'sngt': 'sangat',
            'trimakasih': 'terima kasih', 'trmksh': 'terima kasih',
            'mksh': 'makasih', 'mksih': 'makasih',
            'plng': 'paling', 'pake': 'pakai',
            'karna': 'karena', 'krna': 'karena',
            'pnting': 'penting', 'pntng': 'penting',
            'gede': 'besar', 'gd': 'besar',
            'jelek': 'jelek', 'jlek': 'jelek',
            'bnyk': 'banyak', 'bnyak': 'banyak',
            'sdikit': 'sedikit', 'sdkit': 'sedikit',
            'krja': 'kerja', 'kerj': 'kerja',
            'org': 'orang', 'orng': 'orang',
            'trus': 'terus', 'trs': 'terus',
            'brp': 'berapa', 'brpa': 'berapa',
            'gmn': 'gimana', 'gmna': 'gimana', 'bgmn': 'bagaimana',
            'kmrn': 'kemarin', 'kmren': 'kemarin',
            'smpai': 'sampai', 'smpe': 'sampai', 'smpei': 'sampai',
            'smoga': 'semoga', 'smga': 'semoga',
            'mslh': 'masalah', 'mslah': 'masalah',
            'hrs': 'harus', 'hrus': 'harus',
            'kdng': 'kadang', 'kdang': 'kadang',
            'wktu': 'waktu', 'wkt': 'waktu',
            'tmpat': 'tempat', 'tmpt': 'tempat',
        }
        
        # Negation words
        self.negation_words = {'tidak', 'bukan', 'jangan', 'gak', 'ga', 'nggak', 'ngga'}
    
    def preprocess_detailed(self, text):
        """
        Preprocess text dengan menampilkan setiap step
        """
        steps = {}
        steps['original'] = text
        steps['original_length'] = len(text)
        steps['original_words'] = len(text.split())
        
        # 1. Case Folding
        text = text.lower()
        steps['case_folding'] = text
        
        # 2. Noise Removal (URLs, mentions, hashtags)
        text_no_url = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text_clean = re.sub(r'@\w+|#\w+', '', text_no_url)
        steps['noise_removal'] = text_clean
        
        # 3. Remove Numbers
        text_no_num = re.sub(r'\d+', '', text_clean)
        steps['remove_numbers'] = text_no_num
        
        # 4. Remove Punctuation
        text_no_punct = text_no_num.translate(str.maketrans('', '', string.punctuation))
        steps['remove_punctuation'] = text_no_punct
        
        # 5. Normalize Whitespace
        text_normalized = ' '.join(text_no_punct.split())
        steps['normalize_whitespace'] = text_normalized
        
        # 6. Spelling Correction
        tokens_before_spell = text_normalized.split()
        corrected_tokens = [self.spelling_dict.get(token, token) for token in tokens_before_spell]
        text_spell_corrected = ' '.join(corrected_tokens)
        steps['spelling_correction'] = text_spell_corrected
        
        # 7. Tokenization
        tokens = text_spell_corrected.split()
        steps['tokenization'] = tokens
        steps['token_count'] = len(tokens)
        
        # 8. Normalization (Slang to formal)
        normalized_tokens = [self.normalization_dict.get(token, token) for token in tokens]
        steps['normalization'] = normalized_tokens
        
        # 9. Stopword Removal
        text_for_stopword = ' '.join(normalized_tokens)
        try:
            text_no_stopword = self.stopword_remover.remove(text_for_stopword)
            tokens_no_stopword = text_no_stopword.split()
        except:
            tokens_no_stopword = normalized_tokens
        steps['stopword_removal'] = tokens_no_stopword
        steps['tokens_after_stopword'] = len(tokens_no_stopword)
        
        # 10. Stemming
        text_for_stem = ' '.join(tokens_no_stopword)
        try:
            text_stemmed = self.stemmer.stem(text_for_stem)
            tokens_stemmed = text_stemmed.split()
        except:
            tokens_stemmed = tokens_no_stopword
        steps['stemming'] = tokens_stemmed
        
        # 11. Negation Handling (mark negated words)
        tokens_with_negation = []
        is_negated = False
        for token in tokens_stemmed:
            if token in self.negation_words:
                is_negated = True
                tokens_with_negation.append(token)
            elif is_negated:
                tokens_with_negation.append(f"NOT_{token}")
                is_negated = False
            else:
                tokens_with_negation.append(token)
        steps['negation_handling'] = tokens_with_negation
        
        # Final text
        final_text = ' '.join(tokens_stemmed)
        steps['final'] = final_text
        steps['final_words'] = len(tokens_stemmed)
        steps['reduction_rate'] = round((1 - len(tokens_stemmed) / max(len(tokens), 1)) * 100, 1)
        
        return final_text, steps
    
    def preprocess_simple(self, text):
        """
        Simple preprocessing without detailed steps (for bulk processing)
        """
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'@\w+|#\w+', '', text)
        text = re.sub(r'\d+', '', text)
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = ' '.join(text.split())
        
        # Spelling correction
        tokens = text.split()
        corrected_tokens = [self.spelling_dict.get(token, token) for token in tokens]
        text = ' '.join(corrected_tokens)
        
        # Normalization
        tokens = text.split()
        normalized_tokens = [self.normalization_dict.get(token, token) for token in tokens]
        text_normalized = ' '.join(normalized_tokens)
        
        try:
            text_no_stopword = self.stopword_remover.remove(text_normalized)
            text_stemmed = self.stemmer.stem(text_no_stopword)
        except:
            text_stemmed = text_normalized
        
        return text_stemmed


class SentimentAnalyzer:
    def __init__(self):
        # Initialize preprocessor
        self.preprocessor = TextPreprocessor()
        
        # Load ALL sentiment lexicon from kamus folder
        self.positive_words = set()
        self.negative_words = set()
        self.sentiwords = {}
        self.boosterwords = {}
        self.emoticons = {}
        self.idioms = {}
        self.negation_words = set()
        self.question_words = set()
        
        # Load all lexicon files
        self._load_all_lexicons()
        
        # Initialize ML-based sentiment analyzer
        self.ml_analyzer = MLSentimentAnalyzer(
            self.positive_words,
            self.negative_words,
            self.sentiwords,
            self.boosterwords,
            self.emoticons,
            self.negation_words
        )
        
        print(f"[INFO] Loaded {len(self.positive_words)} positive words and {len(self.negative_words)} negative words from lexicon")
        print(f"[INFO] Loaded {len(self.sentiwords)} weighted sentiment words")
        print(f"[INFO] Loaded {len(self.boosterwords)} booster words, {len(self.emoticons)} emoticons")
        print(f"[INFO] Loaded {len(self.negation_words)} negation words, {len(self.idioms)} idioms")
    
    def _load_all_lexicons(self):
        """
        Load ALL lexicon files from kamus folder
        """
        import os
        kamus_dir = 'kamus'
        
        # Load positive words from all sources
        positive_files = ['positive.tsv', 'positive (1).tsv', '_json_inset-pos.txt']
        for filename in positive_files:
            filepath = os.path.join(kamus_dir, filename)
            if os.path.exists(filepath):
                words = self._load_lexicon(filepath)
                self.positive_words.update(words)
        
        # Load negative words from all sources
        negative_files = ['negative.tsv', 'negative (1).tsv', '_json_inset-neg.txt']
        for filename in negative_files:
            filepath = os.path.join(kamus_dir, filename)
            if os.path.exists(filepath):
                words = self._load_lexicon(filepath)
                self.negative_words.update(words)
        
        # Load sentiwords
        senti_files = ['sentiwords_id.txt', '_json_sentiwords_id.txt']
        for filename in senti_files:
            filepath = os.path.join(kamus_dir, filename)
            if os.path.exists(filepath):
                words = self._load_sentiwords(filepath)
                self.sentiwords.update(words)
        
        # Load boosterwords
        booster_file = os.path.join(kamus_dir, 'boosterwords_id.txt')
        if os.path.exists(booster_file):
            self.boosterwords = self._load_weighted_words(booster_file)
        
        # Load emoticons
        emoticon_file = os.path.join(kamus_dir, 'emoticon_id.txt')
        if os.path.exists(emoticon_file):
            self.emoticons = self._load_weighted_words(emoticon_file)
        
        # Load negation words
        negation_file = os.path.join(kamus_dir, 'negatingword.txt')
        if os.path.exists(negation_file):
            self.negation_words = self._load_simple_list(negation_file)
        
        # Load idioms
        idiom_file = os.path.join(kamus_dir, 'idioms_id.txt')
        if os.path.exists(idiom_file):
            self.idioms = self._load_weighted_words(idiom_file)
        
        # Load question words
        question_file = os.path.join(kamus_dir, 'questionword.txt')
        if os.path.exists(question_file):
            self.question_words = self._load_simple_list(question_file)
        
        # Load colloquial words
        colloquial_file = os.path.join(kamus_dir, 'colloquial-indonesian-lexicon.csv')
        if os.path.exists(colloquial_file):
            self._load_colloquial(colloquial_file)
    
    def _load_simple_list(self, filepath):
        """
        Load simple word list (one word per line)
        """
        words = set()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip().lower()
                    if line and not line.startswith('#'):
                        words.add(line)
        except Exception as e:
            print(f"[WARNING] Error loading {filepath}: {e}")
        return words
    
    def _load_weighted_words(self, filepath):
        """
        Load words with weights (format: word:weight or word\tweight)
        """
        words = {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ':' in line:
                            parts = line.split(':')
                        elif '\t' in line:
                            parts = line.split('\t')
                        else:
                            continue
                        
                        if len(parts) >= 2:
                            word = parts[0].strip().lower()
                            try:
                                weight = float(parts[1].strip())
                                words[word] = weight
                            except ValueError:
                                continue
        except Exception as e:
            print(f"[WARNING] Error loading {filepath}: {e}")
        return words
    
    def _load_colloquial(self, filepath):
        """
        Load colloquial Indonesian lexicon
        """
        try:
            import csv
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Add to positive/negative based on sentiment
                    if 'sentiment' in row or 'polarity' in row:
                        word = row.get('word', '').strip().lower()
                        sentiment = row.get('sentiment', row.get('polarity', '')).strip().lower()
                        
                        if word:
                            if sentiment in ['positive', 'positif', 'pos', '1']:
                                self.positive_words.add(word)
                            elif sentiment in ['negative', 'negatif', 'neg', '-1']:
                                self.negative_words.add(word)
        except Exception as e:
            print(f"[WARNING] Error loading colloquial lexicon: {e}")
        print(f"[INFO] Loaded {len(self.boosterwords)} booster words, {len(self.emoticons)} emoticons")
        print(f"[INFO] Loaded {len(self.negation_words)} negation words, {len(self.idioms)} idioms")
    
    def _load_lexicon(self, filepath):
        """
        Load sentiment words from TSV file in kamus folder
        Format: word\tweight
        """
        words = set()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Skip header
                next(f)
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 1:
                            word = parts[0].strip().lower()
                            if word:
                                words.add(word)
        except FileNotFoundError:
            print(f"[WARNING] Lexicon file not found: {filepath}")
        except Exception as e:
            print(f"[ERROR] Failed to load lexicon from {filepath}: {e}")
        
        return words
    
    def _load_sentiwords(self, filepath):
        """
        Load weighted sentiment words from sentiwords file
        Format: word:score
        """
        sentiwords = {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:
                        parts = line.split(':')
                        if len(parts) == 2:
                            word = parts[0].strip().lower()
                            try:
                                score = int(parts[1].strip())
                                if word:
                                    sentiwords[word] = score
                            except ValueError:
                                continue
        except FileNotFoundError:
            print(f"[WARNING] Sentiwords file not found: {filepath}")
        except Exception as e:
            print(f"[ERROR] Failed to load sentiwords from {filepath}: {e}")
        
        return sentiwords
    
    def naive_bayes_analysis(self, text):
        """
        Naive Bayes sentiment analysis using ML
        """
        return self.ml_analyzer.naive_bayes_analysis(text)
    
    def svm_analysis(self, text):
        """
        Support Vector Machine sentiment analysis
        """
        return self.ml_analyzer.svm_analysis(text)
    
    def lstm_analysis(self, text):
        """
        LSTM sentiment analysis
        """
        return self.ml_analyzer.lstm_analysis(text)
    
    def indobert_analysis(self, text):
        """
        IndoBERT sentiment analysis
        """
        return self.ml_analyzer.indobert_analysis(text)
    
    def analyze_multiple_methods(self, comments, selected_methods):
        """
        Analyze comments using multiple methods
        """
        import time
        start_time = time.time()
        
        method_map = {
            'naive_bayes': 'Naive Bayes',
            'svm': 'SVM',
            'lstm': 'LSTM',
            'indobert': 'IndoBERT'
        }
        
        sentiment_map = {
            'positif': 'positive',
            'negatif': 'negative',
            'netral': 'neutral'
        }
        
        results = {
            'comments': [],
            'summary': {},
            'preprocessing_examples': []
        }
        
        # Initialize summary
        for method_key in selected_methods:
            method_name = method_map.get(method_key, method_key)
            results['summary'][method_name] = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        # Get preprocessing examples from first 3 comments
        example_count = 0
        
        # Batch preprocess all comments first (faster than one-by-one)
        print(f"[PERF] Starting preprocessing for {len(comments)} comments...")
        preprocess_start = time.time()
        preprocessed_texts = []
        for comment in comments:
            preprocessed_texts.append(self.preprocessor.preprocess_simple(comment['text']))
        print(f"[PERF] Preprocessing done in {time.time() - preprocess_start:.2f}s")
        
        analyze_start = time.time()
        for idx, comment in enumerate(comments):
            text = comment['text']
            
            # Get detailed preprocessing for first 3 comments only
            if example_count < 3:
                _, preprocessing_steps = self.preprocessor.preprocess_detailed(text)
                results['preprocessing_examples'].append({
                    'comment_index': idx + 1,
                    'author': comment['author'],
                    'steps': preprocessing_steps
                })
                example_count += 1
            
            # Use pre-processed text
            preprocessed = preprocessed_texts[idx]
            
            comment_result = {
                'author': comment['author'],
                'text': text,
                'likes': comment['likes']
            }
            
            # Analyze with selected methods
            if 'naive_bayes' in selected_methods:
                nb_sentiment, nb_score = self.naive_bayes_analysis(preprocessed)
                comment_result['naive_bayes_sentiment'] = nb_sentiment
                comment_result['naive_bayes_score'] = round(nb_score, 3)
                sentiment_key = sentiment_map.get(nb_sentiment.lower(), nb_sentiment.lower())
                results['summary']['Naive Bayes'][sentiment_key] += 1
            
            if 'svm' in selected_methods:
                svm_sentiment, svm_score = self.svm_analysis(preprocessed)
                comment_result['svm_sentiment'] = svm_sentiment
                comment_result['svm_score'] = round(svm_score, 3)
                sentiment_key = sentiment_map.get(svm_sentiment.lower(), svm_sentiment.lower())
                results['summary']['SVM'][sentiment_key] += 1
            
            if 'lstm' in selected_methods:
                lstm_sentiment, lstm_score = self.lstm_analysis(preprocessed)
                comment_result['lstm_sentiment'] = lstm_sentiment
                comment_result['lstm_score'] = round(lstm_score, 3)
                sentiment_key = sentiment_map.get(lstm_sentiment.lower(), lstm_sentiment.lower())
                results['summary']['LSTM'][sentiment_key] += 1
            
            if 'indobert' in selected_methods:
                indobert_sentiment, indobert_score = self.indobert_analysis(preprocessed)
                comment_result['indobert_sentiment'] = indobert_sentiment
                comment_result['indobert_score'] = round(indobert_score, 3)
                sentiment_key = sentiment_map.get(indobert_sentiment.lower(), indobert_sentiment.lower())
                results['summary']['IndoBERT'][sentiment_key] += 1
            
            results['comments'].append(comment_result)
        
        print(f"[PERF] Sentiment analysis done in {time.time() - analyze_start:.2f}s")
        print(f"[PERF] Total analyze_multiple_methods: {time.time() - start_time:.2f}s for {len(comments)} comments")
        
        # Calculate accuracy and confusion matrix for each method
        if len(selected_methods) > 1:
            results['accuracy'] = self._calculate_cross_method_accuracy(results['comments'], selected_methods)
            results['confusion_matrices'] = self._generate_confusion_matrices(results['comments'], selected_methods)
        
        return results
    
    def _calculate_cross_method_accuracy(self, analyzed_comments, methods):
        """
        Calculate agreement accuracy between methods
        Uses majority voting as ground truth
        """
        from collections import Counter
        
        accuracy_scores = {}
        
        # Get all predictions per comment
        all_predictions = {method: [] for method in methods}
        
        for comment in analyzed_comments:
            predictions_for_comment = []
            
            for method in methods:
                method_name = method.replace('_', ' ').title()
                sentiment_key = f"{method}_sentiment"
                
                if sentiment_key in comment:
                    sentiment = comment[sentiment_key]
                    all_predictions[method].append(sentiment)
                    predictions_for_comment.append(sentiment)
            
            # Majority vote as "ground truth"
            if predictions_for_comment:
                majority = Counter(predictions_for_comment).most_common(1)[0][0]
                
                # Calculate agreement for each method
                for method in methods:
                    sentiment_key = f"{method}_sentiment"
                    if sentiment_key in comment:
                        if method not in accuracy_scores:
                            accuracy_scores[method] = {'correct': 0, 'total': 0}
                        
                        accuracy_scores[method]['total'] += 1
                        if comment[sentiment_key] == majority:
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
    
    def _generate_confusion_matrices(self, analyzed_comments, methods):
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
        for comment in analyzed_comments:
            predictions = []
            for method in methods:
                sentiment_key = f"{method}_sentiment"
                if sentiment_key in comment:
                    predictions.append(comment[sentiment_key])
            
            if predictions:
                majority = Counter(predictions).most_common(1)[0][0]
                majority_votes.append(majority)
            else:
                majority_votes.append('Netral')
        
        # Build confusion matrix for each method
        for method in methods:
            matrix = np.zeros((3, 3), dtype=int)
            
            for idx, comment in enumerate(analyzed_comments):
                sentiment_key = f"{method}_sentiment"
                if sentiment_key in comment and idx < len(majority_votes):
                    predicted = comment[sentiment_key]
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
    
    def generate_confusion_matrix_images(self, confusion_matrices):
        """
        Generate confusion matrix visualization images
        Returns base64 encoded images
        """
        import seaborn as sns
        
        images = {}
        
        for method, cm_data in confusion_matrices.items():
            matrix = np.array(cm_data['matrix'])
            labels = cm_data['labels']
            
            # Create figure
            plt.figure(figsize=(6, 5))
            
            # Plot confusion matrix
            sns.heatmap(
                matrix,
                annot=True,
                fmt='d',
                cmap='Blues',
                xticklabels=labels,
                yticklabels=labels,
                cbar_kws={'label': 'Count'}
            )
            
            method_name = method.replace('_', ' ').title()
            plt.title(f'Confusion Matrix - {method_name}', fontsize=14, fontweight='bold')
            plt.ylabel('Actual (Majority Vote)', fontsize=11)
            plt.xlabel('Predicted', fontsize=11)
            plt.tight_layout()
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            images[method] = image_base64
        
        return images
    
    def generate_wordcloud(self, analyzed_comments):
        """
        Generate dual wordclouds (positive and negative) from analyzed comments
        """
        import time
        start_time = time.time()
        
        positive_texts = []
        negative_texts = []
        
        # Use already analyzed data
        for comment in analyzed_comments:
            # Get sentiment from any available method (prefer naive_bayes)
            sentiment = comment.get('naive_bayes_sentiment') or comment.get('svm_sentiment') or comment.get('lstm_sentiment') or comment.get('indobert_sentiment')
            
            if sentiment and 'Positif' in sentiment:
                positive_texts.append(comment['text'])
            elif sentiment and 'Negatif' in sentiment:
                negative_texts.append(comment['text'])
        
        result = {}
        
        # Generate positive wordcloud
        if positive_texts:
            # Simple preprocessing for wordcloud
            all_positive = ' '.join(positive_texts)
            all_positive = self.preprocessor.preprocess_simple(all_positive)
            
            wordcloud_pos = WordCloud(
                width=600,
                height=300,
                background_color='white',
                colormap='Greens',
                max_words=50,
                relative_scaling=0.5,
                min_font_size=10
            ).generate(all_positive)
            
            img_buffer = BytesIO()
            plt.figure(figsize=(8, 4))
            plt.imshow(wordcloud_pos, interpolation='bilinear')
            plt.axis('off')
            plt.title('Kata-kata dalam Komentar Positif', fontsize=14, pad=15)
            plt.tight_layout(pad=0)
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=80)
            plt.close()
            
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            result['positive'] = f"data:image/png;base64,{img_base64}"
            result['positive_count'] = len(positive_texts)
        else:
            result['positive'] = None
            result['positive_count'] = 0
        
        # Generate negative wordcloud
        if negative_texts:
            # Simple preprocessing for wordcloud
            all_negative = ' '.join(negative_texts)
            all_negative = self.preprocessor.preprocess_simple(all_negative)
            
            wordcloud_neg = WordCloud(
                width=600,
                height=300,
                background_color='white',
                colormap='Reds',
                max_words=50,
                relative_scaling=0.5,
                min_font_size=10
            ).generate(all_negative)
            
            img_buffer = BytesIO()
            plt.figure(figsize=(8, 4))
            plt.imshow(wordcloud_neg, interpolation='bilinear')
            plt.axis('off')
            plt.title('Kata-kata dalam Komentar Negatif', fontsize=14, pad=15)
            plt.tight_layout(pad=0)
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=80)
            plt.close()
            
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            result['negative'] = f"data:image/png;base64,{img_base64}"
            result['negative_count'] = len(negative_texts)
        else:
            result['negative'] = None
            result['negative_count'] = 0
        
        print(f"[PERF] Wordcloud generation: {time.time() - start_time:.2f}s (Positive: {result.get('positive_count', 0)}, Negative: {result.get('negative_count', 0)})")
        
        return result
