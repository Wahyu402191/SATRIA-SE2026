import nltk
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from wordcloud import WordCloud
import re
import string
import json
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
            'bgt': 'banget', 'bngtt': 'banget', 'bngeet': 'banget',
            'bgus': 'bagus', 'bgs': 'bagus',
            'tp': 'tapi', 'tpi': 'tapi',
            'yg': 'yang', 'sy': 'saya',
            'dr': 'dari', 'dri': 'dari',
            'jd': 'jadi', 'jdi': 'jadi',
            'krn': 'karena', 'krna': 'karena',
            'dgn': 'dengan', 'sm': 'sama',
            'emg': 'emang', 'emng': 'emang',
            'bkn': 'bukan', 'ad': 'ada',
            # Common YouTube comment slang
            'keren': 'keren', 'mantap': 'mantap', 'mantul': 'mantap',
            'anjay': 'hebat', 'anjir': 'hebat', 'anjrit': 'hebat',
            'wkwk': 'lucu', 'wkwkw': 'lucu', 'haha': 'lucu', 'hehe': 'lucu',
            'wow': 'hebat', 'wah': 'hebat', 'woow': 'hebat',
            'ampun': 'hebat', 'dah': 'hebat',
            'jelek': 'jelek', 'jlek': 'jelek', 'buruk': 'buruk',
            'parah': 'buruk', 'ancur': 'buruk', 'hancur': 'buruk',
            'gila': 'hebat', 'gilak': 'hebat', 'gilaa': 'hebat',
            'kece': 'bagus', 'cakep': 'bagus', 'cantik': 'bagus',
            'seru': 'menarik', 'asik': 'menarik', 'asyik': 'menarik',
            'bosen': 'membosankan', 'boring': 'membosankan',
            'males': 'malas', 'malesin': 'malas',
        }
        # Fill gaps from the ~15,500-entry slang->formal lexicon (kamus/
        # colloquial-indonesian-lexicon.csv) — previously wired into the
        # sentiment lexicon loader as if it were sentiment-labeled data,
        # where it silently matched nothing (its columns are slang/formal,
        # not sentiment/polarity). Hand-curated entries above always win.
        self._load_colloquial_normalization()

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

        # Full Indonesian stopword list (kamus/id.stopwords.02.01.2016.txt,
        # 757 words) minus negation words — negation words must survive
        # tokenization so ml_sentiment_analyzer.py's negation-flip logic can
        # still see them; every other grammatical/function word (pada,
        # sebagai, hanya, menurut, kata, ujar, ...) is dropped before
        # sentiment scoring, since the tiny ~45-word set previously used
        # here let most of them through.
        self.stop_words_full = self._load_stopwords_file() - self.negation_words

    def _load_stopwords_file(self):
        import os
        filepath = os.path.join('kamus', 'id.stopwords.02.01.2016.txt')
        words = set()
        if not os.path.exists(filepath):
            return words
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip().lower()
                    if line:
                        words.add(line)
        except Exception as e:
            print(f"[WARNING] Error loading stopwords: {e}")
        return words

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
        Fast preprocessing for bulk analysis — NO Sastrawi stemming.
        Sastrawi is ~1-2s per call which makes bulk analysis unusably slow.
        Simple regex + dict normalization is ~1000x faster and nearly as accurate
        for lexicon-based sentiment scoring.
        
        For SHORT texts (YouTube comments, tweets), uses minimal stopword removal
        to preserve sentiment-bearing context. For LONG texts (news articles),
        uses full stopword list to reduce noise.
        """
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'@\w+|#\w+', '', text)
        text = re.sub(r'\d+', '', text)
        # Collapse repeated letters ("parahhh", "mantappp", "sadiss") to a
        # normal 1-2 letter run so these land on the same lexicon entry as
        # their plain spelling — comments lean on letter-stretching for
        # emphasis constantly and none of those variants existed in the
        # lexicon as separate words.
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        # Emoji glued directly onto a word with no space ("setuju👍👍👍")
        # used to survive as one unmatchable token — give emoji their own
        # whitespace boundary so the word underneath can still match.
        text = re.sub(r'([\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF])', r' \1 ', text)
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = ' '.join(text.split())

        # Spelling + slang normalization (combined dict lookup — O(n) per token)
        combined = {**self.spelling_dict, **self.normalization_dict}
        tokens = [combined.get(t, t) for t in text.split()]

        # Count words to determine if text is short (comment) or long (article)
        word_count = len(tokens)
        
        if word_count <= 30:
            # SHORT TEXT (YouTube comments): minimal stopword removal
            # Only remove pure grammar words, keep intensifiers and sentiment carriers
            minimal_stopwords = {
                'yang', 'di', 'ke', 'dari', 'untuk', 'pada', 'dengan', 'oleh',
                'adalah', 'ini', 'itu', 'dan', 'atau', 'serta', 'tetapi',
                'karena', 'jika', 'maka', 'akan', 'telah', 'sudah', 'sedang',
                'bila', 'jadi', 'namun', 'lalu', 'kemudian', 'saat', 'ketika',
                'bagi', 'antara', 'atas', 'bawah', 'dalam', 'luar', 'kami',
                'kita', 'mereka', 'ia', 'dia', 'nya', 'mu', 'ku', 'nya'
            }
            # PRESERVE negation and intensifiers
            tokens = [t for t in tokens if t and (t not in minimal_stopwords or t in self.negation_words) and len(t) > 1]
        else:
            # LONG TEXT (news articles): full stopword removal
            # Use full 757-word list minus negation words
            tokens = [t for t in tokens if t and t not in self.stop_words_full and len(t) > 1]

        return ' '.join(tokens)

    def preprocess_simple_with_sastrawi(self, text):
        """
        Full preprocessing WITH Sastrawi — use only when needed (single text, detail view).
        """
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'@\w+|#\w+', '', text)
        text = re.sub(r'\d+', '', text)
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = ' '.join(text.split())

        tokens = text.split()
        corrected_tokens = [self.spelling_dict.get(token, token) for token in tokens]
        text = ' '.join(corrected_tokens)

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
    
    # Common bureaucratic/administrative nouns that ended up net-negative in
    # the source lexicons (apparently from the corpora they were built on)
    # but carry no inherent sentiment in Indonesian news/government-statistics
    # text — e.g. "data" and "petugas" appear in nearly every BPS article,
    # and scoring them negative systematically biased classification toward
    # Negatif regardless of the article's actual tone. Neutralized (removed
    # from both sets) rather than moved to positive, since there's no
    # evidence they're positive either — just not sentiment-bearing.
    NEUTRALIZE_WORDS = {
        'data', 'jamin', 'menjamin', 'petugas', 'instansi', 'wajib',
        'kota', 'realisasi',
        # Same issue, found while chasing why results still felt noisy after
        # the first pass: ordinary census/reporting vocabulary that shows up
        # in nearly every SE2026 article regardless of tone (e.g. "usaha" is
        # literally the census's subject noun — a business/enterprise unit —
        # not "effort"), so tagging it pos/neg injects near-random sentiment
        # into almost every single article rather than reflecting real tone.
        'unit', 'usaha', 'laporan', 'pelaksanaan', 'mitra', 'pendataan',
        'capaian', 'kegiatan', 'pengumpulan', 'lapangan', 'koordinator',
        # Institutional/descriptive nouns for this exact domain — "badan",
        # "pusat", "statistik" are literally three of the four words in
        # "Badan Pusat Statistik" itself, so of course they're in almost
        # every article regardless of tone.
        'statistik', 'kebijakan', 'pusat', 'badan', 'informasi', 'resmi',
        'proses', 'tingkat', 'sosial',
        # Manual word-by-word audit pass over the remaining sentiment-tagged
        # words still showing up among the most frequent words in real
        # articles. Checked each against actual usage in scraped content
        # before deciding — plain neutral nouns/verbs/numbers, or words whose
        # real usage here is a fixed neutral phrase rather than the
        # standalone meaning the lexicon scored:
        #   - "salah" is scored as negative ("wrong"), but by far its most
        #     common appearance in these articles is inside "salah satu"
        #     ("one of ...") — a completely neutral phrase.
        #   - "kepentingan" only ever appears here as "untuk kepentingan X"
        #     ("for the purposes of X") — bureaucratic phrasing, not the
        #     emotionally-loaded sense of "self-interest".
        #   - "potensi", "memahami" show up in genuinely mixed-tone contexts
        #     in this corpus (e.g. "berpotensi tidak...", "belum memahami
        #     tujuan..."), so a fixed positive score misrepresents them as
        #     often as it fits.
        #   - "kualitas" (the noun, "quality") is neutral on its own — good
        #     or bad quality both use the same word — unlike "berkualitas"
        #     ("high-quality", kept positive) which does inherently mean
        #     good quality.
        'persen', 'rumah', 'hasil', 'membaca', 'berita', 'dunia', 'keluarga',
        'terkait', 'struktur', 'perubahan', 'perusahaan', 'mikro', 'fondasi',
        'juta', 'perkembangan', 'bentuk', 'tugas', 'kerja', 'langsung',
        'sesuai', 'menerima', 'memperoleh', 'salah', 'potensi', 'kualitas',
        'kepentingan', 'memahami',
        # Same audit repeated against real YouTube comment text (a very
        # different register from news articles — short, informal,
        # conversational filler words) after the YouTube dashboard showed a
        # heavy, suspicious Negatif skew (56-66% across all 4 methods).
        # Checked actual comment excerpts before deciding:
        #   - "ya"/"kayak"/"biar"/"coba" are pure discourse fillers/
        #     conjunctions here ("ya pak", "kayak gini", "biar bisa",
        #     "coba jawab") — not expressing genuine sentiment — yet "ya"
        #     alone carried +12 and appeared 155 times, the single largest
        #     contributor to the whole dataset's positive/negative noise.
        #   - "tau"/"cari"/"lihat"/"masuk" are neutral cognitive/action verbs
        #     ("gak tau gunanya", "cari petugas yg cerdas", "masuk akal") —
        #     same category as "memahami"/"menerima" already fixed above.
        #   - "anak"/"hidup"/"jaman"/"pekerjaan"/"pendapatan" are plain nouns
        #     (child, life, era, job, income) that only read as negative
        #     because THIS video's comments are largely critical in tone —
        #     the words themselves aren't sentiment-bearing.
        #   - "suruh"/"tinggal"/"habis"/"mending" are neutral
        #     command/temporal/comparative function words.
        #   - "pejabat" (government official) is a job-title noun exactly
        #     like "petugas" above — neutralized for the same reason, even
        #     though it's used cynically in this particular comment section.
        #   - "banget" was double-counted: it's correctly in boosterwords
        #     (an intensifier that multiplies the NEXT word's score) but was
        #     ALSO sitting in positive_words with its own +3, so it added
        #     spurious positive weight on top of its multiplier role.
        'ya', 'kayak', 'biar', 'coba', 'tau', 'cari', 'mencari', 'lihat',
        'masuk', 'anak', 'hidup', 'jaman', 'pekerjaan', 'pendapatan', 'suruh',
        'tinggal', 'habis', 'mending', 'pejabat', 'kekayaan', 'banget',
    }

    def _load_all_lexicons(self):
        """
        Load ALL lexicon files from kamus folder.

        Positive/negative word lists are merged by NET WEIGHT across every
        source file rather than by plain set union: several source files
        disagree on individual words (e.g. "usaha" is -4 in negative.tsv but
        +1 in positive.tsv), and a plain union left ~1,150 words in BOTH
        self.positive_words and self.negative_words simultaneously, silently
        counting toward both tallies for any text containing them. Summing
        each word's weight across all sources and keeping only the sign of
        the total resolves this in a principled, data-driven way — a word
        only ends up positive/negative if its sources agree on balance.
        """
        import os
        kamus_dir = 'kamus'

        net_weight = {}

        def accumulate(files, sign):
            for filename in files:
                filepath = os.path.join(kamus_dir, filename)
                if not os.path.exists(filepath):
                    continue
                for word, weight in self._load_weighted_lexicon(filepath).items():
                    # Files are inconsistent about whether "negative" weights
                    # are already stored as negative numbers or as plain
                    # magnitudes — normalize using abs() * sign so a file's
                    # role (positive vs negative source) always wins over
                    # whatever sign convention it happens to use internally.
                    net_weight[word] = net_weight.get(word, 0.0) + sign * abs(weight)

        accumulate(['positive.tsv', 'positive (1).tsv', '_json_inset-pos.txt'], +1)
        accumulate(['negative.tsv', 'negative (1).tsv', '_json_inset-neg.txt'], -1)

        # kamus/id.stopwords.02.01.2016.txt (757 grammatical/function words —
        # "tidak", "pada", "sebagai", "hanya", "menurut", "kata", "ujar", ...)
        # was sitting unused in the folder (no code referenced it anywhere).
        # The pos/neg source files score plenty of these on their own (e.g.
        # "tidak": -15, "pada": -9) despite them being pure grammar/reporting-
        # verb vocabulary with no sentiment of their own — and since they're
        # some of the most frequent words in any Indonesian sentence, that
        # injected near-random noise into almost every single article. This
        # includes negation words like "tidak"/"bukan" themselves: they still
        # do their negation-flipping job via the separate self.negation_words
        # set (used by ml_sentiment_analyzer.py to flip the NEXT word's
        # score) — they just shouldn't ALSO carry an independent sentiment
        # score of their own.
        self.stopwords_all = self._load_simple_list(os.path.join(kamus_dir, 'id.stopwords.02.01.2016.txt'))

        # Common YouTube comment sentiment words (often missing from formal
        # lexicons, which are mostly built from formal writing, not social
        # media slang). Grouped by category below; only words with a clear,
        # largely context-independent charge are included — pure sarcasm
        # markers like "wkwk"/"haha" are deliberately left out, since people
        # laugh both mockingly and genuinely and a lexicon can't tell those
        # apart (tagging them would just trade one kind of noise for another).
        youtube_positive = {
            # Quality / praise slang
            'keren': 3, 'mantap': 3, 'mantul': 3, 'gokil': 2, 'gacor': 2,
            'topcer': 3, 'jempolan': 3, 'sip': 2, 'sippp': 2, 'worth': 2,
            'worthit': 3, 'memukau': 3, 'ciamik': 3, 'apik': 2,
            'anjay': 2, 'anjir': 2, 'hebat': 3, 'bagus': 3, 'lucu': 2,
            'seru': 2, 'asik': 2, 'asyik': 2, 'wow': 2, 'wah': 2, 'gila': 2,
            'gilak': 2, 'kece': 3, 'cakep': 3, 'cantik': 3, 'menarik': 2,
            'top': 3, 'oke': 1, 'ok': 1, 'nice': 2, 'sukses': 3,
            'berhasil': 3, 'sempurna': 3, 'terbaik': 3,
            # Emotion
            'senang': 2, 'suka': 2, 'cinta': 3, 'love': 3, 'bahagia': 3,
            'gembira': 3, 'bangga': 3, 'kagum': 2, 'terharu': 2,
            'bersyukur': 3, 'syukur': 2,
            # Trust / good governance (relevant to this survey's own domain)
            'amanah': 3, 'adil': 3, 'keadilan': 2, 'transparan': 3,
            'transparansi': 2, 'akuntabel': 2, 'tanggungjawab': 2,
            'bertanggungjawab': 2,
        }
        youtube_negative = {
            'jelek': -3, 'jlek': -3, 'buruk': -3, 'parah': -3, 'ancur': -3,
            'hancur': -3, 'bosen': -2, 'boring': -2, 'males': -2, 'malesin': -2,
            'payah': -2, 'gagal': -3, 'mengecewakan': -3, 'kecewa': -3,
            'sedih': -2, 'susah': -2, 'sulit': -2, 'ribet': -2,
            'ngeselin': -2, 'kesel': -2, 'marah': -3, 'benci': -3,
            # Found missing while auditing real comments that were landing
            # Netral purely for lack of ANY matched lexicon word (not a
            # threshold issue) — these are common in cynical/political
            # comment threads like this dataset's ("koruptor", "percuma
            # bertanya", "pejabat korup") but absent from every source file.
            'koruptor': -3, 'korup': -3, 'percuma': -3, 'kritisi': -2,
            'mengkritisi': -2, 'menipu': -3, 'tertipu': -3, 'bohong': -3,
            'dibohongi': -3, 'zalim': -3,
            # Corruption / distrust of officials — extremely common register
            # in Indonesian government-related comment sections
            'maling': -3, 'pencuri': -3, 'mencuri': -3, 'nyolong': -3,
            'ditilep': -3, 'ditilap': -3, 'dipalak': -3, 'memalak': -3,
            'memeras': -3, 'pemerasan': -3, 'culas': -3, 'licik': -3,
            'munafik': -3, 'khianat': -3, 'mengkhianati': -3, 'penipu': -3,
            'tipu': -2, 'pencitraan': -2, 'settingan': -2, 'sandiwara': -2,
            'akting': -1, 'ingkar': -2, 'mangkrak': -2, 'molor': -2,
            # Quality complaints / dismissive slang
            'berantakan': -2, 'amburadul': -3, 'kacau': -2, 'ngaco': -2,
            'gaje': -2, 'norak': -2, 'alay': -1, 'lebay': -1, 'receh': -1,
            # Insults
            'goblok': -3, 'tolol': -3, 'bego': -2, 'bodoh': -2,
            'songong': -2, 'sombong': -2, 'angkuh': -2, 'arogan': -2,
            # Futility / hardship
            'siasia': -2, 'mubazir': -2, 'sengsara': -3, 'menderita': -3,
            'melarat': -3, 'tercekik': -2, 'terjepit': -2,
            # Anger (beyond what's already above)
            'sebel': -2, 'sewot': -2, 'geram': -2, 'murka': -3,
        }
        
        # Merge YouTube words into net_weight
        for word, weight in youtube_positive.items():
            net_weight[word] = net_weight.get(word, 0.0) + weight
        for word, weight in youtube_negative.items():
            net_weight[word] = net_weight.get(word, 0.0) + weight

        self.lexicon_weights = net_weight
        self.positive_words = {w for w, s in net_weight.items() if s > 0} - self.NEUTRALIZE_WORDS - self.stopwords_all
        self.negative_words = {w for w, s in net_weight.items() if s < 0} - self.NEUTRALIZE_WORDS - self.stopwords_all

        # Load sentiwords (weighted, finer-grained than the pos/neg sets).
        # _lexicon_score() in ml_sentiment_analyzer.py checks this dict
        # BEFORE positive_words/negative_words, so it needs the exact same
        # stopword/domain-noun cleanup or contamination leaks back in
        # through this second path (e.g. "resmi": +4 and "sementara": -1
        # were still here even after cleaning the pos/neg sets above).
        senti_files = ['sentiwords_id.txt', '_json_sentiwords_id.txt']
        for filename in senti_files:
            filepath = os.path.join(kamus_dir, filename)
            if os.path.exists(filepath):
                self.sentiwords.update(self._load_weighted_lexicon(filepath))
        for w in (self.NEUTRALIZE_WORDS | self.stopwords_all):
            self.sentiwords.pop(w, None)

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

        # colloquial-indonesian-lexicon.csv is a slang→formal normalization
        # table (columns: slang, formal, ...), not a sentiment lexicon — it's
        # loaded into TextPreprocessor.normalization_dict instead (see
        # text_preprocessor.py), so there's nothing to load here anymore.

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

    def _load_weighted_lexicon(self, filepath):
        """
        Load a word->weight lexicon, auto-detecting the file's actual format
        instead of assuming from its name/extension:
          - JSON object (files like `_json_inset-pos.txt` are real JSON
            despite the .txt extension — previously parsed as tab-separated,
            which silently turned every entry into a garbage string like
            '"jamin": -5,' that could never match any real word, discarding
            roughly half of the merged lexicon's coverage without error)
          - TSV with a header row (`word\\tweight`)
          - `word:weight` (one per line)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"[WARNING] Error loading {filepath}: {e}")
            return {}

        stripped = content.lstrip()
        if stripped.startswith('{'):
            try:
                data = json.loads(content)
                return {str(k).strip().lower(): float(v) for k, v in data.items()}
            except Exception as e:
                print(f"[ERROR] Failed to parse {filepath} as JSON: {e}")
                return {}

        words = {}
        lines = content.splitlines()
        # Skip a literal "word\tweight" header row if present
        if lines and lines[0].strip().lower() in ('word\tweight', 'word,weight'):
            lines = lines[1:]
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t') if '\t' in line else line.split(':')
            if len(parts) < 2:
                continue
            word = parts[0].strip().lower()
            try:
                weight = float(parts[1].strip())
            except ValueError:
                continue
            if word:
                words[word] = weight
        return words
    
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
        Analyze comments using batch processing — optimized for speed.
        """
        import time
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
            'netral':  'neutral',
        }

        results = {
            'comments': [],
            'summary': {},
            'preprocessing_examples': [],
        }
        for method_key in selected_methods:
            results['summary'][method_map.get(method_key, method_key)] = {
                'positive': 0, 'negative': 0, 'neutral': 0
            }

        n = len(comments)

        # ── Step 1: batch preprocess with Sastrawi ────────────────────────
        # Sastrawi stemmer is the slowest part — run it once per comment
        print(f"[PERF] Preprocessing {n} comments …")
        t0 = time.time()
        preprocessed_texts = [
            self.preprocessor.preprocess_simple(c['text']) for c in comments
        ]
        print(f"[PERF] Preprocessing done in {time.time()-t0:.2f}s")

        # Gather 3 detailed examples (done separately, not in the hot loop)
        for idx in range(min(3, n)):
            _, steps = self.preprocessor.preprocess_detailed(comments[idx]['text'])
            results['preprocessing_examples'].append({
                'comment_index': idx + 1,
                'author':        comments[idx]['author'],
                'steps':         steps,
            })

        # ── Step 2: batch ML inference ────────────────────────────────────
        print(f"[PERF] Running batch inference …")
        t1 = time.time()
        batch_results = self.ml_analyzer.predict_batch(preprocessed_texts, selected_methods)
        print(f"[PERF] Batch inference done in {time.time()-t1:.2f}s")

        # ── Step 3: merge results ─────────────────────────────────────────
        for idx, comment in enumerate(comments):
            br = batch_results[idx]
            comment_result = {
                'comment_id': comment.get('comment_id'),
                'author': comment['author'],
                'text':   comment['text'],
                'likes':  comment['likes'],
            }

            if 'naive_bayes' in selected_methods:
                label = br['naive_bayes_sentiment']
                comment_result['naive_bayes_sentiment'] = label
                comment_result['naive_bayes_score']     = br['naive_bayes_score']
                key = sentiment_map.get(label.lower(), label.lower())
                results['summary']['Naive Bayes'][key] += 1

            if 'svm' in selected_methods:
                label = br['svm_sentiment']
                comment_result['svm_sentiment'] = label
                comment_result['svm_score']     = br['svm_score']
                key = sentiment_map.get(label.lower(), label.lower())
                results['summary']['SVM'][key] += 1

            if 'lstm' in selected_methods:
                label = br['lstm_sentiment']
                comment_result['lstm_sentiment'] = label
                comment_result['lstm_score']     = br['lstm_score']
                key = sentiment_map.get(label.lower(), label.lower())
                results['summary']['LSTM'][key] += 1

            if 'indobert' in selected_methods:
                label = br['indobert_sentiment']
                comment_result['indobert_sentiment'] = label
                comment_result['indobert_score']     = br['indobert_score']
                key = sentiment_map.get(label.lower(), label.lower())
                results['summary']['IndoBERT'][key] += 1

            results['comments'].append(comment_result)

        print(f"[PERF] Total analyze_multiple_methods: {time.time()-start_time:.2f}s for {n} comments")

        if len(selected_methods) > 1:
            results['accuracy']          = self._calculate_cross_method_accuracy(results['comments'], selected_methods)
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
        Generate dual wordclouds (positive and negative) from analyzed comments.
        Uses majority vote across all available methods for sentiment label.
        """
        import time
        from collections import Counter
        start_time = time.time()

        positive_texts = []
        negative_texts = []

        sentiment_keys = [
            'naive_bayes_sentiment', 'svm_sentiment',
            'lstm_sentiment', 'indobert_sentiment'
        ]

        for comment in analyzed_comments:
            # Collect all available sentiments for this comment
            votes = [comment[k] for k in sentiment_keys if comment.get(k)]
            if not votes:
                continue
            # Majority vote
            sentiment = Counter(votes).most_common(1)[0][0]

            if 'Positif' in sentiment:
                positive_texts.append(comment['text'])
            elif 'Negatif' in sentiment:
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
