import re
import string
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

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
    def __init__(self):
        # Indonesian tools
        self.stemmer_factory = StemmerFactory()
        self.stemmer = self.stemmer_factory.create_stemmer()
        
        self.stopword_factory = StopWordRemoverFactory()
        self.stopword_remover = self.stopword_factory.create_stop_word_remover()
        
        # Stopwords (Indonesian + English)
        self.stop_words_id = set(self.stopword_factory.get_stop_words())
        try:
            self.stop_words_en = set(stopwords.words('english'))
        except:
            self.stop_words_en = set()
        self.stop_words = self.stop_words_id.union(self.stop_words_en)
        
        # Negation words
        self.negation_words = {
            'tidak', 'bukan', 'jangan', 'belum', 'tanpa', 'kurang',
            'no', 'not', 'never', 'none', 'neither', 'nobody', 'nothing'
        }
        
        # Normalization dictionary (slang to formal)
        self.normalization_dict = {
            # Common Indonesian slang
            'gak': 'tidak',
            'ga': 'tidak',
            'gk': 'tidak',
            'ngga': 'tidak',
            'nggak': 'tidak',
            'enggak': 'tidak',
            'gue': 'saya',
            'gw': 'saya',
            'ane': 'saya',
            'lo': 'kamu',
            'lu': 'kamu',
            'elu': 'kamu',
            'loe': 'kamu',
            'yg': 'yang',
            'dgn': 'dengan',
            'utk': 'untuk',
            'tdk': 'tidak',
            'sdh': 'sudah',
            'blm': 'belum',
            'jd': 'jadi',
            'krn': 'karena',
            'kpd': 'kepada',
            'bgt': 'banget',
            'bgt': 'sekali',
            'klo': 'kalau',
            'gmn': 'bagaimana',
            'gmna': 'bagaimana',
            'knp': 'kenapa',
            'knpa': 'kenapa',
            'emg': 'memang',
            'emang': 'memang',
            'tp': 'tapi',
            'tq': 'terima kasih',
            'thx': 'terima kasih',
            'thanks': 'terima kasih',
            'pls': 'tolong',
            'plz': 'tolong',
            'btw': 'ngomong ngomong',
            'fyi': 'untuk informasi',
            # Repeated characters
            'bangettt': 'banget',
            'kerennn': 'keren',
            'bagusss': 'bagus',
            'jelek': 'jelek',
        }

        # kamus/colloquial-indonesian-lexicon.csv is a ~15,500-entry
        # slang -> formal Indonesian table. It was previously wired into
        # sentiment_analyzer.py as if it were a sentiment lexicon (checking
        # for 'sentiment'/'polarity' columns that don't exist in this file,
        # so it silently contributed zero words there). It belongs here
        # instead — more slang normalized before sentiment matching means
        # more lexicon hits downstream. Loaded additively: the hand-curated
        # entries above always win over the CSV for the same slang word.
        self._load_colloquial_normalization()

    def _load_colloquial_normalization(self):
        import csv
        import os
        filepath = os.path.join('kamus', 'colloquial-indonesian-lexicon.csv')
        if not os.path.exists(filepath):
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    slang = (row.get('slang') or '').strip().lower()
                    formal = (row.get('formal') or '').strip().lower()
                    if slang and formal and slang not in self.normalization_dict:
                        self.normalization_dict[slang] = formal
        except Exception as e:
            print(f"[WARNING] Error loading colloquial normalization lexicon: {e}")

    def case_folding(self, text):
        """
        Convert text to lowercase
        """
        return text.lower()
    
    def remove_noise(self, text):
        """
        Remove URLs, mentions, hashtags, emails, numbers
        """
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove mentions
        text = re.sub(r'@\w+', '', text)
        
        # Remove hashtags
        text = re.sub(r'#\w+', '', text)
        
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        return text
    
    def remove_punctuation(self, text):
        """
        Remove all punctuation marks
        """
        return text.translate(str.maketrans('', '', string.punctuation))
    
    def normalize_text(self, text):
        """
        Normalize slang words and repeated characters
        """
        # Remove repeated characters (more than 2)
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        
        # Normalize words using dictionary
        words = text.split()
        normalized_words = []
        for word in words:
            normalized_word = self.normalization_dict.get(word.lower(), word)
            normalized_words.append(normalized_word)
        
        return ' '.join(normalized_words)
    
    def tokenize(self, text):
        """
        Tokenize text into words
        """
        try:
            tokens = word_tokenize(text)
        except:
            # Fallback to simple split if NLTK fails
            tokens = text.split()
        return tokens
    
    def remove_stopwords(self, tokens):
        """
        Remove stopwords from tokens
        """
        filtered_tokens = [word for word in tokens if word.lower() not in self.stop_words]
        return filtered_tokens
    
    def stem_text(self, tokens):
        """
        Apply stemming to tokens (Indonesian)
        """
        # Join tokens for Sastrawi (it works on full text)
        text = ' '.join(tokens)
        stemmed_text = self.stemmer.stem(text)
        return stemmed_text.split()
    
    def handle_negation(self, tokens):
        """
        Handle negation by marking negated words
        """
        processed_tokens = []
        negate = False
        
        for i, token in enumerate(tokens):
            if token.lower() in self.negation_words:
                negate = True
                processed_tokens.append(token)
            elif negate:
                # Mark the next word as negated
                processed_tokens.append(f"NOT_{token}")
                negate = False
            else:
                processed_tokens.append(token)
        
        return processed_tokens
    
    def preprocess_full(self, text, options=None):
        """
        Full preprocessing pipeline
        
        Options:
        - case_folding: True/False
        - remove_noise: True/False
        - remove_punctuation: True/False
        - normalize: True/False
        - tokenize: True/False
        - remove_stopwords: True/False
        - stemming: True/False
        - handle_negation: True/False
        """
        if options is None:
            options = {
                'case_folding': True,
                'remove_noise': True,
                'remove_punctuation': True,
                'normalize': True,
                'tokenize': True,
                'remove_stopwords': True,
                'stemming': True,
                'handle_negation': True
            }
        
        # Store original
        original_text = text
        
        # Step 1: Case Folding
        if options.get('case_folding', True):
            text = self.case_folding(text)
        
        # Step 2: Remove Noise
        if options.get('remove_noise', True):
            text = self.remove_noise(text)
        
        # Step 3: Remove Punctuation
        if options.get('remove_punctuation', True):
            text = self.remove_punctuation(text)
        
        # Step 4: Normalize
        if options.get('normalize', True):
            text = self.normalize_text(text)
        
        # Step 5: Tokenize
        if options.get('tokenize', True):
            tokens = self.tokenize(text)
        else:
            tokens = text.split()
        
        # Step 6: Remove Stopwords
        if options.get('remove_stopwords', True):
            tokens = self.remove_stopwords(tokens)
        
        # Step 7: Stemming
        if options.get('stemming', True):
            tokens = self.stem_text(tokens)
        
        # Step 8: Handle Negation
        if options.get('handle_negation', True):
            tokens = self.handle_negation(tokens)
        
        # Remove empty tokens and extra spaces
        tokens = [t.strip() for t in tokens if t.strip()]
        
        return {
            'original': original_text,
            'processed': ' '.join(tokens),
            'tokens': tokens
        }
    
    def preprocess_simple(self, text):
        """
        Simple preprocessing for sentiment analysis
        (without removing too much information)
        """
        # Case folding
        text = self.case_folding(text)
        
        # Remove noise
        text = self.remove_noise(text)
        
        # Normalize
        text = self.normalize_text(text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
