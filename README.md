# SATRIA SE2026

Scraping and Sentiment Analysis Tracker for Economic Census 2026 — BPS Kabupaten Bangkalan.

Aplikasi web berbasis Flask untuk mengambil komentar dari video YouTube dan menganalisis sentimennya menggunakan 4 metode Machine Learning (Naive Bayes, SVM, LSTM, IndoBERT).

## Fitur

- Scraping komentar YouTube via YouTube Data API v3 (hingga 100.000 komentar)
- Analisis sentimen 4 metode ML: Naive Bayes, SVM, LSTM, IndoBERT
- Filter dan sort komentar berdasarkan sentimen
- Visualisasi word cloud dan confusion matrix
- Trend kata per waktu (chart per bulan)
- Export hasil ke Excel (.xlsx) dan cetak laporan PDF
- Detail 12 langkah preprocessing teks (NLP)

## Cara Menjalankan

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Konfigurasi API Key

Buat file `.env` di folder project dan isi dengan:

```
YOUTUBE_API_KEY=api_key_youtube_anda
SECRET_KEY=secret_key_bebas
PORT=5000
FLASK_DEBUG=true
```

Dapatkan YouTube API Key di: https://console.cloud.google.com (aktifkan YouTube Data API v3)

### 3. Jalankan server

```
python app.py
```

Buka browser di `http://localhost:5000`

### 4. Foto gedung BPS (opsional)

Taruh file foto dengan nama `bps-bangkalan.jpg` di folder `static/img/` agar tampil di header.

## Teknologi

- Python 3, Flask
- scikit-learn (Naive Bayes, SVM), Sastrawi, NLTK
- pandas, matplotlib, WordCloud
- YouTube Data API v3
