# 📦 Panduan Instalasi SATRIA SE2026

## Langkah 1: Persiapan Environment

### 1.1 Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Catatan:** Jika ada error saat install `mysql-connector-python`, coba alternatif:
```bash
pip install pymysql
```

## Langkah 2: Setup MySQL Database

### 2.1 Start MySQL Server (XAMPP)
1. Buka **XAMPP Control Panel**
2. Klik **Start** pada module **MySQL**
3. Tunggu hingga status menjadi hijau (running)

### 2.2 Import Database Schema

#### **Cara 1: Via phpMyAdmin (Recommended)**
1. Buka browser, akses: `http://localhost/phpmyadmin`
2. Klik tab **Import**
3. Klik **Choose File**, pilih file `database.sql`
4. Scroll ke bawah, klik **Go**
5. Tunggu hingga muncul pesan sukses

#### **Cara 2: Via MySQL Command Line**
```bash
mysql -u root -p < database.sql
```
*(Jika diminta password dan tidak ada, tekan Enter saja)*

### 2.3 Verifikasi Database
1. Buka phpMyAdmin
2. Pastikan database **satria_se2026** sudah ada
3. Klik database tersebut, pastikan terdapat tabel:
   - `videos`
   - `comments`
   - `analysis_results`
   - `analysis_sessions`

## Langkah 3: Konfigurasi Environment

### 3.1 Check File `.env`
Pastikan file `.env` sudah memiliki konfigurasi MySQL:

```env
# MySQL Database Configuration (XAMPP)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=satria_se2026
```

**Penting:**
- Jika MySQL Anda pakai password, isi `MYSQL_PASSWORD=your_password`
- Jika port MySQL bukan 3306, ubah `MYSQL_PORT`

## Langkah 4: Test Koneksi Database

### 4.1 Test via Python
```bash
python db_config.py
```

**Output yang diharapkan:**
```
[✓] MySQL connection pool initialized successfully
[✓] Connected to MySQL database: satria_se2026 (version 10.4.x)
[✓] All required tables exist: videos, comments, analysis_results, analysis_sessions
```

**Jika ada error:**
- Pastikan MySQL sudah running di XAMPP
- Pastikan database sudah di-import
- Check credentials di `.env`

## Langkah 5: Jalankan Aplikasi

```bash
python app.py
```

**Output yang diharapkan:**
```
[✓] DataStorage initialized with MySQL backend
[✓] MySQL connection pool initialized successfully
 * Running on http://0.0.0.0:5000
```

Buka browser: `http://localhost:5000`

## 🔧 Troubleshooting

### Error: "No module named 'mysql'"
```bash
pip install mysql-connector-python
```

### Error: "Can't connect to MySQL server"
1. Pastikan MySQL running di XAMPP
2. Check port di Task Manager (default 3306)
3. Restart MySQL service di XAMPP

### Error: "Database 'satria_se2026' doesn't exist"
1. Import ulang file `database.sql`
2. Atau buat manual via phpMyAdmin

### Error: "Table doesn't exist"
- Import ulang file `database.sql`
- Pastikan import tidak ada error

### Aplikasi berjalan tapi stats = 0
- Normal jika belum ada data scraping
- Lakukan scraping pertama untuk populate database

## 📊 Fitur Baru dengan MySQL

1. **Dashboard Statistics** - Real-time count videos, comments, dan analisis
2. **Data Persistence** - Data tidak hilang setelah restart aplikasi
3. **Query Performance** - Pencarian dan filter lebih cepat
4. **Data Integrity** - Relasi antar tabel terjaga (CASCADE delete)
5. **Backup Ready** - Bisa export via phpMyAdmin

## 🗂️ Struktur Database

```
satria_se2026/
├── videos              → Data video YouTube yang discrape
├── comments            → Komentar dari video (with replies)
├── analysis_results    → Hasil analisis sentimen per metode
├── analysis_sessions   → Log session analisis
└── (views)             → Agregasi dan summary
```

## 🔄 Migrasi dari JSON ke MySQL

**Catatan:** Aplikasi masih menyimpan backup JSON di folder `data/` sebagai fallback. Jika MySQL tidak available, aplikasi akan gunakan JSON mode otomatis.

---

**Dibuat oleh:** BPS Kabupaten Bangkalan  
**Project:** SATRIA SE2026 — Scraping & Sentiment Analysis Tracker for Economic Census 2026
