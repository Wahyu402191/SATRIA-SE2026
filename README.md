# SATRIA SE2026

**Sistem Analisis Tren & Riset Informasi Augmentasi — Sensus Ekonomi 2026**  
Badan Pusat Statistik Kabupaten Bangkalan

Aplikasi web terintegrasi untuk analisis sentimen multi-sumber menggunakan 4 metode Machine Learning dengan optimasi parallel processing.

---

## 📋 Daftar Isi

- [Arsitektur Sistem](#arsitektur-sistem)
- [Teknologi Stack](#teknologi-stack)
- [Fitur Aplikasi](#fitur-aplikasi)
- [Cara Menjalankan](#cara-menjalankan)
- [Struktur Database](#struktur-database)
- [Dokumentasi API](#dokumentasi-api)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ Arsitektur Sistem

### Backend Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Application                     │
│                      (app.py)                           │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼─────────┐ ┌──────▼──────┐ ┌─────────▼────────┐
│  YouTube Module │ │ Media Massa │ │   Berita SE2026  │
│                 │ │   Module    │ │      Module      │
│ - Scraper       │ │ - Analyzer  │ │  - RSS Scraper   │
│ - Storage       │ │ - Storage   │ │  - Analyzer      │
│ - Analyzer      │ │             │ │  - Storage       │
└─────────────────┘ └─────────────┘ └──────────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                ┌───────────▼───────────┐
                │  ML Sentiment Engine  │
                │  (Parallel Processing)│
                │                       │
                │  ┌─────────────────┐ │
                │  │  Naive Bayes    │ │
                │  │  SVM            │◄├─ ThreadPoolExecutor
                │  │  LSTM           │ │   (4 workers)
                │  │  IndoBERT       │ │
                │  └─────────────────┘ │
                └───────────────────────┘
                            │
                ┌───────────▼───────────┐
                │    MySQL Database     │
                │   (satria_se2026)     │
                └───────────────────────┘
```

### Frontend Architecture

```
┌─────────────────────────────────────────┐
│         Jinja2 Templates                │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Base Template (base.html)      │   │
│  │  - Navigation                   │   │
│  │  - Footer                       │   │
│  │  - Common Scripts               │   │
│  └─────────────────────────────────┘   │
│           │                             │
│  ┌────────┴────────┬──────────────┐    │
│  │                 │              │    │
│  ▼                 ▼              ▼    │
│ YouTube        Media Massa    SE2026   │
│ Templates      Templates      Templates│
└─────────────────────────────────────────┘
            │
    ┌───────┴───────┐
    ▼               ▼
JavaScript      CSS/Styling
- Chart.js      - Modern UI
- Fetch API     - Animations
- DOM Manip.    - Responsive
```

---

## 🛠️ Teknologi Stack

### Backend

| Komponen | Teknologi | Versi | Fungsi |
|----------|-----------|-------|--------|
| **Framework** | Flask | 3.x | Web framework |
| **Database** | MySQL/MariaDB | 10.4+ | Persistent storage |
| **ORM** | MySQL Connector | 8.x | Database interface |
| **ML Framework** | scikit-learn | 1.3+ | Naive Bayes, SVM |
| **Deep Learning** | TensorFlow/Keras | (Simulasi) | LSTM, IndoBERT |
| **NLP** | Sastrawi, NLTK | Latest | Text preprocessing |
| **Scheduling** | APScheduler | 3.x | Background jobs |
| **HTTP Client** | Requests | 2.x | API calls |
| **HTML Parsing** | BeautifulSoup4 | 4.x | Web scraping |
| **RSS Parsing** | feedparser | 6.x | RSS feeds |

### Frontend

| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| **Template Engine** | Jinja2 | Server-side rendering |
| **Charting** | Chart.js | Grafik interaktif |
| **Styling** | Custom CSS | Modern UI design |
| **Icons** | SVG/Font Icons | UI icons |
| **JS Framework** | Vanilla JS | Client-side logic |

### Database Schema

**11 tabel utama:**
- `videos`, `comments`, `analysis_results` (YouTube)
- `news_articles`, `news_sources`, `news_analysis_results` (Media Massa)
- `se_news_articles`, `se_news_sentiment`, `se_news_fetch_log` (Berita SE2026)
- `users`, `analysis_sessions` (Auth & Sessions)

---

## 🎯 Fitur Aplikasi

### 1. YouTube Sentiment Analysis (`/youtube/`)

Analisis sentimen komentar YouTube dengan 4 metode ML secara paralel.

#### Menu & Fitur:

**📍 Beranda (`/youtube/`)**
- **Form Scraping:**
  - Input URL video (youtube.com/watch?v=, youtu.be/, embed/)
  - Jumlah komentar (1-100,000) - default: 1000
  - Include replies (checkbox)
  - Tombol "Mulai Scraping" → scraping real-time dengan progress bar
- **Daftar Video:**
  - Card untuk setiap video yang pernah di-scrape
  - Info: title, channel, views, likes, total comments
  - Tombol "Lihat Komentar" & "Analisis Sentimen"

**📍 Komentar (`/youtube/comments/<video_id>`)**
- **Statistik Header:**
  - Total komentar terscrape
  - Filter by sentiment (All/Positif/Negatif/Netral)
  - Search bar (cari dalam teks komentar)
- **Tabel Komentar:**
  - Author, text, likes, published date
  - Pagination (50 per halaman)
  - Sort by likes, date

**📍 Analisis (`/youtube/analysis/<video_id>`)**
- **Pilih Metode:**
  - Checkbox: Naive Bayes, SVM, LSTM, IndoBERT
  - Tombol "Jalankan Analisis" (parallel processing)
- **Loading:**
  - Progress indicator dengan estimasi waktu
  - "Menganalisis X komentar dengan 4 metode..."
- **Hasil Analisis:**
  - **Distribusi Sentimen per Metode:**
    - Pie chart (Positif/Negatif/Netral)
    - Persentase & jumlah absolut
  - **Confusion Matrix per Metode:**
    - Heatmap 3x3 (Predicted vs Actual)
    - Accuracy score
  - **Wordcloud:**
    - Positif: kata-kata dengan sentimen positif
    - Negatif: kata-kata dengan sentimen negatif
  - **Trend Sentimen:**
    - Line chart: perubahan sentimen dari waktu ke waktu
    - Grouped by publish date
  - **Perbandingan Metode:**
    - Bar chart: persentase Positif/Negatif/Netral per metode
    - Tabel agreement: seberapa sering metode setuju

**📍 Perbandingan (`/youtube/comparison`)**
- Bandingkan hasil analisis antar video
- Multi-select video yang sudah dianalisis
- Side-by-side comparison charts

**📍 Tentang (`/youtube/about`)**
- Penjelasan 4 metode ML
- Cara kerja aplikasi
- Limitasi & disclaimer

---

### 2. Media Massa Analysis (`/media_massa/`)

Analisis sentimen berita media massa (data import manual dari CSV).

#### Menu & Fitur:

**📍 Beranda (`/media_massa/`)**
- **Statistik Overview:**
  - Cards per bulan: Januari - November 2026
  - Jumlah berita per bulan
  - Klik card → filter otomatis ke bulan tersebut

**📍 Analisis (`/media_massa/analysis`)**
- **Filter:**
  - Rentang tanggal (date picker)
  - Pilih metode ML (4 checkbox)
  - Tombol "Mulai Analisis Sentimen"
- **Hasil:**
  - Loading dengan parallel processing (3-4x lebih cepat)
  - Summary statistics per metode
  - Distribusi sentimen (pie charts)
  - Top positive/negative keywords
  - Export ke Excel

**📍 Data Berita (`/media_massa/articles`)**
- **Filter & Search:**
  - Filter by month (dropdown)
  - Filter by source (multi-select)
  - Search by keyword
  - Filter by sentiment
- **Tabel Berita:**
  - Title, source, published date, sentiment (4 metode)
  - Pagination
  - Click row → detail berita

**📍 Perbandingan (`/media_massa/comparison`)**
- Bandingkan sentimen antar bulan
- Line chart: trend sentimen bulanan
- Bar chart: distribusi per sumber media

**📍 Trend (`/media_massa/trend`)**
- Heatmap: intensitas berita per tanggal
- Top sources by article count
- Sentiment flow: perubahan sentimen dari waktu ke waktu

**📍 Tentang (`/media_massa/about`)**
- Sumber data (CSV files)
- Metodologi analisis
- Disclaimer

---

### 3. Berita SE2026 (`/news/`)

Monitoring otomatis berita Sensus Ekonomi 2026 via Google News RSS.

#### Menu & Fitur:

**📍 Beranda (`/news/`)**
- **Status Card:**
  - Last fetch: timestamp terakhir
  - Fetch status: Success/Failed
  - Total articles: jumlah berita terkumpul
  - Tombol "Refresh Berita Sekarang" (manual trigger)
- **Quick Stats:**
  - Berita hari ini
  - Berita minggu ini
  - Berita bulan ini
  - Top sources
- **Recent Articles:**
  - 10 berita terbaru
  - Title, source, published date, snippet

**📍 Data Berita (`/news/articles`)**
- **Advanced Filter:**
  - Tanggal spesifik / rentang tanggal
  - Sumber media (dropdown dari database)
  - Kata kunci (search in title & content)
  - Filter by sentiment (jika sudah dianalisis)
- **Tabel Berita:**
  - Title (clickable → full article)
  - Source, published date
  - Sentiment badges (4 metode)
  - View count, scrape status
- **Pagination:**
  - 50 per halaman
  - Jump to page
  - Total count

**📍 Statistik Harian (`/news/daily`)**
- **Month Selector:**
  - Dropdown: Januari - Desember 2026
  - Otomatis load data bulan terpilih
- **Calendar View:**
  - Grid: 1-31 tanggal
  - Setiap tanggal menampilkan:
    - Jumlah berita (badge)
    - Warna intensitas (gradient)
    - Click → list berita tanggal tersebut
- **Chart:**
  - Bar chart: jumlah berita per hari
  - Line chart: cumulative count

**📍 Analisis Sentimen (`/news/analysis`)**
- **Form:**
  - Rentang tanggal untuk analisis
  - Pilih metode ML (4 checkbox)
  - Tombol "Jalankan Analisis"
- **Processing:**
  - Progress bar dengan parallel processing
  - Real-time update: "Menganalisis artikel X/Y..."
- **Hasil:**
  - **Summary per Metode:**
    - Positif/Negatif/Netral count & percentage
    - Pie chart untuk setiap metode
  - **Agreement Analysis:**
    - Berapa persen 4 metode sepakat?
    - Confusion matrix antar metode
  - **Keyword Analysis:**
    - Wordcloud positif & negatif
    - Top 20 keywords per sentiment
  - **Timeline:**
    - Sentiment change over time (line chart)
    - Stacked area chart: Positif/Netral/Negatif per hari
  - **Export:**
    - Download hasil (Excel, CSV, JSON)

**📍 Trend & Insight (`/news/trend`)**
- **Sentiment Trend:**
  - Line chart: persentase Positif/Negatif/Netral per hari
  - Smoothing option (7-day moving average)
  - Annotation untuk event penting
- **Source Analysis:**
  - Bar chart: jumlah berita per sumber
  - Pie chart: market share per media
  - Table: sentiment distribution per sumber
- **Heatmap:**
  - Kalender 1 tahun penuh (Januari - Desember 2026)
  - Color intensity: jumlah berita per hari
  - Hover → tooltip dengan detail
- **Insight Cards:**
  - Hari dengan berita terbanyak
  - Sumber paling aktif
  - Sentiment dominan per bulan
  - Peak hours (jika ada timestamp)

**📍 Tentang (`/news/about`)**
- **Cara Kerja:**
  - Penjelasan Google News RSS
  - Query terms yang digunakan
  - Frequency (setiap 3 jam)
- **Keterbatasan:**
  - Tidak semua berita terscrape penuh (paywall)
  - Historis data tergantung indeks Google
  - Relevance filtering
- **Konfigurasi:**
  - Cara ubah query terms di `.env`
  - Cara ubah interval fetch
  - Cara disable scheduler

---

### 4. Tentang (`/tentang`)

Informasi umum aplikasi, tim, dan kontak.

---

### 5. Footer Menu (di semua halaman)

**Navigasi:**
- Beranda (redirect ke dashboard utama)
- YouTube Analysis
- Media Massa Analysis
- Berita SE2026
- Tentang

**Copyright:**
- © 2026 BPS Kabupaten Bangkalan
- SATRIA SE2026

---

## 🚀 Cara Menjalankan

### Prasyarat

- **Python 3.10+**
- **MySQL/MariaDB** (via XAMPP atau standalone)
- **4GB RAM** minimum (untuk ML models)

### Instalasi

1. **Clone Repository**
```bash
git clone https://github.com/Wahyu402191/SATRIA-SE2026.git
cd SATRIA-SE2026
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup Database**

**Via phpMyAdmin:**
- Buka XAMPP → Start MySQL → Admin
- Import file: `satria_se2026 (1).sql` (database lengkap dengan data)
- Atau `database.sql` (hanya struktur, tanpa data)

**Via Command Line:**
```bash
mysql -u root < "satria_se2026 (1).sql"
```

4. **Konfigurasi `.env`**
```env
# YouTube API Key (wajib untuk scraping)
YOUTUBE_API_KEY=AIzaSyC...your_key_here

# Database
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=satria_se2026

# Flask
SECRET_KEY=ganti-dengan-random-string-panjang
FLASK_DEBUG=true

# Berita SE2026 Scheduler
SE_NEWS_SCHEDULER_ENABLED=true
SE_NEWS_FETCH_INTERVAL_HOURS=3
SE_NEWS_QUERY_TERMS=Sensus Ekonomi 2026,SE2026 BPS,Sensus Ekonomi BPS
```

**Cara dapat YouTube API Key:**
1. https://console.cloud.google.com → Create Project
2. Enable "YouTube Data API v3"
3. Create Credentials → API Key
4. Copy & paste ke `.env`

5. **Jalankan Aplikasi**

**Via Batch File (Windows):**
```bash
Jalankan_SATRIA_SE2026.bat
```

**Via Python:**
```bash
python app.py
```

6. **Akses di Browser**
```
http://127.0.0.1:5000
```

### Login

| Email | Password | Role |
|-------|----------|------|
| admin@bps.go.id | admin123 | Administrator |
| operator@bps.go.id | operator123 | Operator |
| demo@example.com | demo123 | Demo User |

---

## 🗄️ Struktur Database

### Tabel YouTube Module

**`videos`**
```sql
- id (PK)
- video_id (unique, indexed)
- video_url
- title
- channel
- views, likes, total_comments
- scraped_at, published_at
```

**`comments`**
```sql
- id (PK)
- video_id (FK → videos.video_id)
- comment_id (unique)
- author, text, likes
- published_at
- reply_to (untuk nested replies)
```

**`analysis_results`**
```sql
- id (PK)
- analysis_session_id (FK)
- comment_id (FK → comments.comment_id)
- method (naive_bayes/svm/lstm/indobert)
- sentiment (Positif/Negatif/Netral)
- confidence_score
- analyzed_at
```

### Tabel Media Massa Module

**`news_articles`**
```sql
- id (PK)
- title, content, url
- source (FK → news_sources.source_name)
- published_date, month, year
- imported_at
```

**`news_sources`**
```sql
- id (PK)
- source_name (unique)
- description, website_url
- created_at
```

**`news_analysis_results`**
```sql
- id (PK)
- article_id (FK → news_articles.id)
- method_name
- sentiment, confidence_score
- analyzed_at
```

### Tabel Berita SE2026 Module

**`se_news_articles`**
```sql
- id (PK)
- title, url, url_hash (unique)
- source, rss_snippet
- published_date, query_keyword
- content, content_source (scraped/rss_snippet)
- resolved_url, scrape_status
- fetched_at, scraped_at
```

**`se_news_sentiment`**
```sql
- id (PK)
- article_id (FK → se_news_articles.id)
- analysis_batch_id
- method (naive_bayes/svm/lstm/indobert)
- sentiment, confidence
- analyzed_at
```

**`se_news_fetch_log`**
```sql
- id (PK)
- trigger_type (scheduler/manual)
- started_at, completed_at
- articles_found, articles_new
- articles_scraped_ok, articles_scraped_failed
- status, error_message
```

### Tabel Auth & Sessions

**`users`**
```sql
- id (PK)
- email (unique), password (hashed)
- name, role
- created_at, last_login
```

**`analysis_sessions`**
```sql
- id (PK)
- video_id (FK)
- methods_used (JSON array)
- created_at, updated_at
```

---

## 📊 Optimasi Performa

### Parallel Processing (ML Models)

**Sebelum optimasi:**
```
Naive Bayes → SVM → LSTM → IndoBERT (Sequential)
100 berita = ~40 detik
```

**Setelah optimasi:**
```
┌─ Naive Bayes ─┐
├─ SVM         ─┤  → ThreadPoolExecutor (4 workers)
├─ LSTM        ─┤
└─ IndoBERT    ─┘
100 berita = ~12 detik (3.3x lebih cepat!)
```

**Implementasi:**
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        'naive_bayes': executor.submit(predict_nb, texts),
        'svm': executor.submit(predict_svm, texts),
        'lstm': executor.submit(predict_lstm, texts),
        'indobert': executor.submit(predict_indobert, texts),
    }
```

### Database Indexing

- `video_id` (unique index)
- `comment_id` (unique index)
- `published_date` (index untuk sorting/filtering)
- `sentiment` (index untuk filtering)
- `url_hash` (unique index untuk deduplication)

---

## 🔧 Troubleshooting

### Aplikasi Tidak Bisa Diakses

**Cek Port:**
```bash
netstat -ano | findstr :5000
```

**Ganti Port:**
Edit `.env`:
```
PORT=5001
```

### YouTube Scraping Gagal

**1. Cek API Key:**
```bash
python test_youtube_api.py
```

**2. Video Komentar Dinonaktifkan:**
- Coba video lain
- Tidak semua video bisa di-scrape

**3. Quota Habis:**
- YouTube API gratis: 10,000 requests/hari
- 1 video + 100 komentar ≈ 2-3 requests
- Tunggu 24 jam untuk reset

### Scraping Hanya Dapat 100 Komentar

**Ubah jumlah di form scraping:**
- Default: 1000
- Max: 100,000
- Ubah angka sebelum klik "Mulai Scraping"

### Google RSS Tidak Update

**1. Cek Scheduler:**
Lihat di log aplikasi:
```
[✓] Berita SE2026 scheduler started (every 3h)
```

**2. Manual Refresh:**
- Buka `/news/`
- Klik "Refresh Berita Sekarang"

**3. Cek Log:**
```sql
SELECT * FROM se_news_fetch_log ORDER BY started_at DESC LIMIT 5;
```

### Analisis Sentimen Lama/Hang

**1. Terlalu Banyak Data:**
- Kurangi rentang tanggal
- Pilih 1-2 metode saja (bukan 4)

**2. Memory Kurang:**
- Minimal 4GB RAM
- Close aplikasi lain

**3. Restart Aplikasi:**
```bash
CTRL+C
python app.py
```

### Database Connection Error

**1. MySQL Belum Running:**
- Buka XAMPP Control Panel
- Start MySQL

**2. Password Salah:**
- Cek `.env` → `MYSQL_PASSWORD`
- Default: kosong (no password)

**3. Database Tidak Ada:**
```sql
CREATE DATABASE satria_se2026;
```

### Error saat Import SQL

**File Too Large (phpMyAdmin):**

Edit `php.ini`:
```ini
upload_max_filesize = 50M
post_max_size = 50M
max_execution_time = 300
```

Restart Apache di XAMPP.

---

## 📝 Generate Data Dummy

### Media Massa (2,370 berita Jan-Nov 2026)
```bash
python generate_data_sampai_november.py
```

Output:
- 2,370 berita
- 20 sumber media
- 9,480 hasil analisis (4 metode x 2,370)
- Distribusi realistis per bulan

### YouTube (contoh)
```bash
python generate_youtube_dummy.py
```

Output:
- 3 video populer
- 300 komentar (100 per video)

**Note:** Untuk data real, scrape manual via aplikasi web.

---

## 📂 Struktur Project

```
SATRIA-SE2026/
├── app.py                          # Main application
├── requirements.txt                # Dependencies
├── .env                            # Configuration
├── database.sql                    # DB structure only
├── satria_se2026 (1).sql           # DB with data (18MB)
│
├── static/                         # Static assets
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/                      # Jinja2 templates
│   ├── base.html
│   ├── index.html                  # YouTube dashboard
│   ├── analysis.html               # YouTube analysis
│   ├── media_massa/
│   │   ├── index.html
│   │   └── analysis.html
│   └── news/                       # SE2026 templates
│       ├── index.html
│       ├── articles.html
│       ├── daily.html
│       ├── analysis.html
│       └── trend.html
│
├── youtube_scraper.py              # YouTube API wrapper
├── sentiment_analyzer.py           # Base sentiment logic
├── ml_sentiment_analyzer.py        # 4 ML models (parallel)
├── text_preprocessor.py            # NLP preprocessing
│
├── data_storage.py                 # YouTube DB interface
├── media_massa_analyzer.py         # Media massa logic
├── media_massa_storage.py          # Media massa DB
├── se_news_scraper.py              # RSS scraper
├── se_news_analyzer.py             # SE2026 sentiment
├── se_news_storage.py              # SE2026 DB
├── se_news_scheduler.py            # APScheduler jobs
│
├── auth_storage.py                 # User authentication
├── db_config.py                    # MySQL config
│
├── kamus/                          # Sentiment lexicons
│   ├── positive.txt
│   ├── negative.txt
│   ├── sentiwords_id.txt
│   └── ...
│
├── data/                           # JSON scraped data
├── data_media_massa/               # CSV imports
│
├── Jalankan_SATRIA_SE2026.bat      # Windows launcher
└── README.md                       # This file
```

---

## 🤝 Kontribusi

Aplikasi ini dikembangkan untuk BPS Kabupaten Bangkalan. Untuk pertanyaan atau kontribusi, hubungi tim IT BPS.

---

## 📄 Lisensi

© 2026 Badan Pusat Statistik Kabupaten Bangkalan. All rights reserved.

---

## 🙏 Acknowledgments

- **BPS Kabupaten Bangkalan** - Data & requirements
- **Google Cloud Platform** - YouTube Data API
- **Google News** - RSS feeds
- **scikit-learn** - ML framework
- **Flask** - Web framework

---

**Version:** 1.0.0  
**Last Updated:** November 16, 2026  
**Maintained by:** Tim IT BPS Kabupaten Bangkalan
