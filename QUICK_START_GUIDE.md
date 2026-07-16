# 🚀 QUICK START GUIDE - SATRIA-SE2026

## Panduan Cepat Menjalankan Aplikasi

---

## 📋 Langkah 1: Setup Database

### A. Buka phpMyAdmin
1. Buka browser, akses: `http://localhost/phpmyadmin`
2. Login dengan user MySQL Anda (biasanya `root` tanpa password)

### B. Import Database
1. Klik tab **"Import"** di phpMyAdmin
2. Klik **"Choose File"**
3. Pilih file: `database.sql` dari folder project ini
4. Klik **"Go"** atau **"Import"**
5. Tunggu sampai muncul pesan sukses

### C. Verifikasi Database
1. Klik database `sentiment_analysis` di sidebar kiri
2. Pastikan ada tabel-tabel berikut:
   - `videos` (untuk YouTube)
   - `comments` (untuk YouTube)
   - `analysis_sessions` (untuk YouTube)
   - `analysis_results` (untuk YouTube)
   - `news_sources` ✨ BARU
   - `news_articles` ✨ BARU
   - `news_analysis_sessions` ✨ BARU
   - `news_analysis_results` ✨ BARU

---

## 📋 Langkah 2: Konfigurasi Database di Code

### Cek file: `db_config.py`
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',           # ← Sesuaikan dengan user MySQL Anda
    'password': '',           # ← Isi password MySQL jika ada
    'database': 'sentiment_analysis'
}
```

**PENTING**: Jika password MySQL Anda tidak kosong, ubah bagian `'password': ''` menjadi password Anda!

---

## 📋 Langkah 3: Install Dependencies

Buka terminal/command prompt di folder project, lalu jalankan:

```bash
pip install -r requirements.txt
```

**Tunggu** sampai semua library terinstall.

---

## 📋 Langkah 4: Jalankan Aplikasi

Di terminal/command prompt yang sama, jalankan:

```bash
python app.py
```

Atau di PowerShell:

```powershell
python app.py
```

### Output yang benar:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in production.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

---

## 📋 Langkah 5: Akses Aplikasi

### Buka browser, akses:
```
http://localhost:5000/
```

atau

```
http://127.0.0.1:5000/
```

### Yang akan muncul:
1. **Landing Page** - Tampilan SATRIA-SE2026 dengan tombol "Masuk Aplikasi"
2. Klik tombol → **Selection Page** dengan 3 pilihan:
   - 📰 Berita Sensus Ekonomi Terbaru
   - 📊 Analisis Sentiment Media Massa ← DASHBOARD BARU!
   - 🎥 Scraping & Analisis Sentiment YouTube ← DASHBOARD EXISTING

---

## 🧪 Testing Aplikasi

### Test 1: Landing & Selection
✅ Akses `http://localhost:5000/`  
✅ Klik "Masuk Aplikasi"  
✅ Harus redirect ke halaman dengan 3 tombol pilihan

### Test 2: Dashboard YouTube (Existing)
✅ Klik tombol "Scraping & Analisis Sentiment YouTube"  
✅ Harus masuk ke dashboard YouTube yang sudah ada  
✅ Test fitur: Scraping, Analisis, Comments, Comparison, Trend, About

### Test 3: Dashboard Media Massa (BARU)
✅ Kembali ke selection page  
✅ Klik tombol "Analisis Sentiment Media Massa"  
✅ Harus masuk ke dashboard Media Massa baru  
✅ Test menu di navbar:
   - Beranda/Analisis
   - Berita (Comments)
   - Perbandingan
   - Trend
   - Tentang

---

## 📊 Cara Input Data Media Massa

### Metode 1: Manual via phpMyAdmin

#### 1. Tambah Sumber Media
```sql
-- Di tab SQL di phpMyAdmin:
INSERT INTO news_sources (source_name, source_url, created_at) 
VALUES 
('CNN Indonesia', 'https://www.cnnindonesia.com', NOW()),
('Kompas', 'https://www.kompas.com', NOW()),
('Detik', 'https://www.detik.com', NOW());
```

#### 2. Tambah Artikel Berita
```sql
-- Contoh untuk bulan Januari 2026:
INSERT INTO news_articles 
(source_id, title, content, url, published_date, month, year, created_at) 
VALUES 
(1, 'Ekonomi Indonesia Tumbuh 5.2%', 
'Badan Pusat Statistik mengumumkan pertumbuhan ekonomi...', 
'https://www.cnnindonesia.com/ekonomi/xxxxx', 
'2026-01-15', 1, 2026, NOW());
```

### Metode 2: Import CSV

#### Format CSV yang dibutuhkan:
```csv
source_name,title,content,url,published_date,month,year
CNN Indonesia,Judul Berita 1,Konten berita 1,https://...,2026-01-15,1,2026
Kompas,Judul Berita 2,Konten berita 2,https://...,2026-01-20,1,2026
```

#### Script Python untuk import (buat file baru: `import_news.py`):
```python
import pandas as pd
import mysql.connector
from db_config import DB_CONFIG

# Baca CSV
df = pd.read_csv('berita_januari_2026.csv')

# Koneksi database
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# Insert data
for _, row in df.iterrows():
    # Cek/tambah source
    cursor.execute(
        "SELECT id FROM news_sources WHERE source_name = %s",
        (row['source_name'],)
    )
    source = cursor.fetchone()
    
    if not source:
        cursor.execute(
            "INSERT INTO news_sources (source_name, created_at) VALUES (%s, NOW())",
            (row['source_name'],)
        )
        source_id = cursor.lastrowid
    else:
        source_id = source[0]
    
    # Insert artikel
    cursor.execute("""
        INSERT INTO news_articles 
        (source_id, title, content, url, published_date, month, year, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
    """, (
        source_id,
        row['title'],
        row['content'],
        row['url'],
        row['published_date'],
        row['month'],
        row['year']
    ))

conn.commit()
cursor.close()
conn.close()
print("Data berhasil diimport!")
```

Jalankan:
```bash
python import_news.py
```

---

## 🎯 Contoh Data untuk Testing

### Data Sample (Copy ke SQL tab di phpMyAdmin):

```sql
-- Tambah sumber media
INSERT INTO news_sources (source_name, source_url, created_at) VALUES
('CNN Indonesia', 'https://www.cnnindonesia.com', NOW()),
('Kompas', 'https://www.kompas.com', NOW()),
('Detik', 'https://www.detik.com', NOW()),
('CNBC Indonesia', 'https://www.cnbcindonesia.com', NOW());

-- Tambah artikel Januari 2026
INSERT INTO news_articles (source_id, title, content, url, published_date, month, year, created_at) VALUES
(1, 'Ekonomi RI Tumbuh Positif di Awal Tahun', 
'Pertumbuhan ekonomi Indonesia di awal tahun 2026 menunjukkan tren positif dengan capaian 5.2 persen...', 
'https://www.cnnindonesia.com/ekonomi/20260115-ekonomi-tumbuh', '2026-01-15', 1, 2026, NOW()),

(2, 'Inflasi Januari Terkendali di Level 2.5%', 
'Badan Pusat Statistik mencatat inflasi Januari 2026 berada di level 2.5 persen, masih dalam target...', 
'https://www.kompas.com/ekonomi/20260120-inflasi-terkendali', '2026-01-20', 1, 2026, NOW()),

(3, 'Rupiah Menguat Terhadap Dolar AS', 
'Nilai tukar rupiah terus mengalami penguatan terhadap dolar Amerika Serikat...', 
'https://www.detik.com/finance/20260125-rupiah-menguat', '2026-01-25', 1, 2026, NOW());

-- Tambah artikel Februari 2026
INSERT INTO news_articles (source_id, title, content, url, published_date, month, year, created_at) VALUES
(1, 'Ekspor Indonesia Meningkat Signifikan', 
'Kinerja ekspor Indonesia di bulan Februari mengalami peningkatan yang signifikan...', 
'https://www.cnnindonesia.com/ekonomi/20260210-ekspor-meningkat', '2026-02-10', 2, 2026, NOW()),

(4, 'Investasi Asing Membludak', 
'Investasi asing langsung ke Indonesia mengalami lonjakan di kuartal pertama 2026...', 
'https://www.cnbcindonesia.com/market/20260215-investasi-asing', '2026-02-15', 2, 2026, NOW());
```

---

## ❓ Troubleshooting

### Problem 1: Error "Module not found"
**Solusi**:
```bash
pip install [nama-module-yang-error]
```
Atau:
```bash
pip install -r requirements.txt
```

### Problem 2: Error koneksi database
**Solusi**:
1. Pastikan XAMPP/MySQL sudah running
2. Cek `db_config.py` - pastikan user, password, dan database name benar
3. Test koneksi manual:
```python
import mysql.connector
from db_config import DB_CONFIG

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    print("✅ Koneksi database berhasil!")
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
```

### Problem 3: Port 5000 sudah digunakan
**Solusi**: Ubah port di `app.py` bagian paling bawah:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # ← Ganti dari 5000 ke 5001
```
Lalu akses: `http://localhost:5001/`

### Problem 4: Template not found
**Solusi**: Pastikan struktur folder benar:
```
SATRIA-SE2026/
├── templates/
│   ├── landing.html
│   ├── selection.html
│   └── (file YouTube lainnya)
├── templates_media_massa/
│   ├── base_media.html
│   ├── index_media.html
│   └── (file media massa lainnya)
└── app.py
```

---

## 📚 Resource & Dokumentasi

- **Project Report**: `PROJECT_COMPLETION_REPORT.md`
- **Testing Checklist**: `TESTING_CHECKLIST.md`
- **This Guide**: `QUICK_START_GUIDE.md`

---

## 🎉 Selamat!

Jika semua langkah di atas berhasil, aplikasi **SATRIA-SE2026** Anda sudah siap digunakan!

### Urutan Akses:
```
http://localhost:5000/
    ↓ (klik Masuk Aplikasi)
http://localhost:5000/selection
    ↓ (pilih salah satu)
    ├→ Dashboard YouTube (existing)
    └→ Dashboard Media Massa (BARU)
```

**Happy coding! 🚀**

---

**Dibuat oleh**: AI Assistant (Kiro)  
**Tanggal**: 16 Juli 2026  
**Versi**: 1.0
