# 🚀 Quick Start — SATRIA SE2026

## Langkah Cepat (5 Menit)

### 1️⃣ Jalankan MySQL (XAMPP)
```
1. Buka XAMPP Control Panel
2. Klik "Start" pada MySQL
3. Tunggu status hijau
```

### 2️⃣ Import Database
```
1. Buka http://localhost/phpmyadmin
2. Klik "Import"
3. Pilih file "database.sql"
4. Klik "Go"
```

### 3️⃣ Jalankan Aplikasi
```bash
python app.py
```

### 4️⃣ Buka Browser
```
http://localhost:5000
```

---

## 🎯 Fitur Baru v2.0

### Dashboard Statistics (Real-time)
- **Total Video** — Berapa video yang sudah discrape
- **Total Komentar** — Jumlah komentar tersimpan di database
- **Analisis** — Jumlah hasil analisis sentimen
- **Metode ML** — 4 metode (NB, SVM, LSTM, IndoBERT)

### Modern UI Elements
- ✨ **Gradient Icon Cards** dengan warna berbeda per kategori
- 📊 **Animated Counters** saat load dashboard
- 🎨 **Professional Feather Icons** (SVG, bukan emoji)
- 🌊 **Smooth Hover Effects** pada semua cards
- 🎬 **Staggered Animations** saat page load

### Database Features
- 💾 **Persistent Storage** — Data tidak hilang setelah restart
- ⚡ **Fast Queries** dengan indexing optimal
- 🔄 **Auto-save Analysis** results
- 🗂️ **Relational Data** dengan CASCADE delete
- 📦 **Backup JSON** tetap dibuat otomatis

---

## 🛠️ Troubleshooting Cepat

### Stats = 0 semua?
✅ **Normal!** Belum ada data. Lakukan scraping pertama.

### MySQL connection error?
1. Pastikan MySQL running di XAMPP
2. Pastikan database sudah di-import
3. Check `.env` file (credentials MySQL)

### Dashboard tidak muncul statistik?
1. Check console browser (F12) untuk error
2. Pastikan endpoint `/get_dashboard_stats` berfungsi
3. Coba refresh (Ctrl+F5)

---

## 📖 Dokumentasi Lengkap

- **INSTALL.md** — Panduan instalasi detail + troubleshooting
- **CHANGELOG.md** — Semua perubahan di v2.0
- **README.md** — Overview project
- **database.sql** — Schema database (sudah di-import)

---

## 🎓 Cara Pakai

### Scraping Komentar
1. Masukkan URL video YouTube
2. Set jumlah komentar (max 100,000)
3. Checklist "Sertakan replies" jika perlu
4. Klik "Mulai Scraping"
5. Tunggu progress bar selesai

### Analisis Sentimen
1. Setelah scraping selesai, klik "Analisis Sentimen"
2. Pilih metode ML yang ingin digunakan (bisa multiple)
3. Klik "Mulai Analisis"
4. Lihat hasil: distribusi, wordcloud, confusion matrix

### Export Data
- **Excel:** Klik "Export ke Excel" (4 sheets: info, comments, summary, accuracy)
- **PDF:** Klik "Export PDF" (laporan siap cetak)

---

## 💡 Tips

- **Scraping 1000+ komentar:** Sabar, prosesnya otomatis batch
- **Analisis cepat:** Gunakan metode Naive Bayes & SVM saja (paling cepat)
- **Analisis akurat:** Gunakan semua 4 metode untuk voting hasil
- **Database backup:** Export via phpMyAdmin secara berkala
- **JSON backup:** Otomatis tersimpan di folder `data/`

---

**Selamat menggunakan SATRIA SE2026! 🎉**

*BPS Kabupaten Bangkalan*
