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

### Prasyarat Sistem
- **Python 3.9+** terinstall
- **MySQL Server** berjalan (XAMPP atau standalone)
- **Git** (opsional, untuk cloning repository)

### Step 1: Clone/Download Project
```bash
# Jika menggunakan git
git clone <repository-url>
cd SATRIA-SE2026

# Atau download ZIP dan ekstrak
```

### Step 2: Buat Virtual Environment (Opsional tapi Direkomendasikan)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```
**Tunggu hingga semua paket selesai diinstall** (~5-10 menit tergantung koneksi)

### Step 4: Setup Database MySQL

#### Option A: Menggunakan XAMPP (Recommended untuk pemula)
1. Buka XAMPP Control Panel
2. Klik tombol **Start** untuk MySQL
3. Klik tombol **Admin** pada MySQL (membuka phpMyAdmin)
4. Di phpMyAdmin:
   - Klik menu **Import**
   - Pilih file `database.sql` dari folder project
   - Klik **Go** untuk mengimport database

#### Option B: Menggunakan Command Line
```bash
mysql -u root < database.sql
```

#### Verifikasi Database
```bash
mysql -u root -e "USE satria_se2026; SHOW TABLES;"
```

Pastikan muncul table: `videos`, `comments`, `analysis_results`

### Step 5: Konfigurasi Environment Variables

Edit file `.env` di root folder:
```env
# YouTube API Configuration
YOUTUBE_API_KEY=AIzaSyBXx_TbElpqMLGH2f73EDr4qqcMj1fkODk
SECRET_KEY=your-secret-key-change-this-in-production
PORT=5000
FLASK_DEBUG=true

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=              # Kosongkan jika tidak punya password
MYSQL_DATABASE=satria_se2026
```

**Dapatkan YouTube API Key:**
1. Buka https://console.cloud.google.com
2. Buat project baru
3. Enable YouTube Data API v3
4. Buat API Key di credentials section
5. Copy-paste key ke file `.env`

### Step 6: Jalankan Aplikasi

#### Dari Command Prompt/Terminal:
```bash
# Aktifkan virtual environment terlebih dahulu (jika ada)
# venv\Scripts\activate

# Jalankan Flask development server
python app.py
```

#### Output yang benar:
```
[✓] MySQL connection pool initialized successfully
[✓] Connected to MySQL database: satria_se2026
[INFO] ML Sentiment Analyzer initialized
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.87:5000
Press CTRL+C to quit
```

### Step 7: Akses Aplikasi

**Buka browser Anda dan kunjungi:**
- **Local:** http://localhost:5000
- **Network:** http://192.168.1.87:5000 (untuk akses dari perangkat lain)

### Fitur yang Tersedia di Dashboard

| Fitur | Deskripsi |
|-------|-----------|
| 📥 **Scrape YouTube** | Input URL video YouTube & scraping komentar |
| 📊 **Analisis Sentimen** | Analisis dengan 4 metode ML (Naive Bayes, SVM, LSTM, IndoBERT) |
| 💾 **Simpan ke Database** | Otomatis menyimpan hasil ke MySQL |
| 📈 **Dashboard** | Visualisasi statistik real-time dari database |
| 📋 **List Komentar** | Filter & sort berdasarkan sentimen (Positif/Negatif/Netral) |
| 📥 **Export Data** | Download hasil dalam format Excel, PDF, CSV |
| 📊 **Wordcloud** | Visualisasi kata-kata yang sering muncul |
| 🎯 **Confusion Matrix** | Evaluasi akurasi model ML |
| 📉 **Trend Kata** | Analisis trend sentimen dari waktu ke waktu |

### Menghentikan Aplikasi
```bash
# Di terminal, tekan:
CTRL + C
```

### Troubleshooting

#### Error: "YOUTUBE_API_KEY belum dikonfigurasi"
- ✅ Edit file `.env` dan tambahkan API Key yang valid
- ✅ Simpan file dan restart aplikasi

#### Error: "Can't connect to MySQL"
- ✅ Pastikan MySQL Server sudah berjalan (check XAMPP)
- ✅ Verifikasi username & password di `.env`
- ✅ Pastikan database `satria_se2026` sudah di-import

#### Error: "ModuleNotFoundError"
- ✅ Pastikan virtual environment sudah aktif
- ✅ Jalankan `pip install -r requirements.txt` kembali
- ✅ Cek Python version: `python --version` (harus 3.9+)

#### Port 5000 sudah dipakai
```bash
# Jalankan di port lain:
export FLASK_PORT=5001  # Linux/Mac
set FLASK_PORT=5001     # Windows
python app.py
```

#### Aplikasi lambat/crash saat scraping
- ✅ Kurangi jumlah komentar yang di-scrape (default: 100.000)
- ✅ Pastikan RAM tersedia minimal 4GB
- ✅ Gunakan model Naive Bayes (tercepat) terlebih dahulu

## Teknologi

- **Backend:** Python 3, Flask
- **Database:** MySQL (via XAMPP)
- **ML:** scikit-learn (Naive Bayes, SVM), LSTM, IndoBERT
- **NLP:** Sastrawi, NLTK, TextBlob
- **Visualisasi:** matplotlib, WordCloud, Chart.js
- **Export:** openpyxl (Excel), HTML to PDF

---

📖 **Troubleshooting & Panduan Detail:** Lihat file `INSTALL.md`
