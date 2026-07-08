# SATRIA SE2026

**Scraping and Sentiment Analysis Tracker for Economic Census 2026**  
Badan Pusat Statistik Kabupaten Bangkalan

Aplikasi web untuk scraping komentar YouTube dan analisis sentimen menggunakan 4 metode Machine Learning (Naive Bayes, SVM, LSTM, IndoBERT) dengan database MySQL.

## Fitur Utama

- Scraping komentar YouTube (hingga 100.000 komentar per video)
- Analisis sentimen dengan 4 metode ML
- **Database MySQL** untuk penyimpanan data permanen
- **Dashboard statistik** real-time dari database
- Filter dan sort komentar berdasarkan sentimen
- Export hasil ke Excel dan PDF
- Visualisasi wordcloud, confusion matrix, dan trend kata
- UI modern dengan animasi elegan

## Cara Menjalankan

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database MySQL
**⚠️ Panduan lengkap ada di file `INSTALL.md`**

Singkatnya:
1. Start MySQL di XAMPP
2. Import file `database.sql` via phpMyAdmin
3. Check konfigurasi di file `.env`

### 3. Konfigurasi API Key

Edit file `.env` dan pastikan terisi:
```env
YOUTUBE_API_KEY=your_youtube_api_key_here
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=satria_se2026
```

Dapatkan YouTube API Key di: https://console.cloud.google.com

### 4. Jalankan Aplikasi
```bash
python app.py
```

Buka browser: `http://localhost:5000`

## Teknologi

- **Backend:** Python 3, Flask
- **Database:** MySQL (via XAMPP)
- **ML:** scikit-learn (Naive Bayes, SVM), LSTM, IndoBERT
- **NLP:** Sastrawi, NLTK, TextBlob
- **Visualisasi:** matplotlib, WordCloud, Chart.js
- **Export:** openpyxl (Excel), HTML to PDF

---

📖 **Troubleshooting & Panduan Detail:** Lihat file `INSTALL.md`
