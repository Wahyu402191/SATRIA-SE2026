# Cara Import Database ke phpMyAdmin

## Cara 1: Via phpMyAdmin (Paling Mudah untuk File Besar)

1. Buka **XAMPP Control Panel**
2. Klik tombol **Start** di MySQL (jika belum jalan)
3. Klik tombol **Admin** di sebelah MySQL (akan membuka phpMyAdmin di browser)
4. Di phpMyAdmin:
   - Klik tab **"Databases"** di menu atas
   - Jika database `satria_se2026` sudah ada, klik nama database tersebut
   - Jika belum ada, buat dulu dengan nama `satria_se2026` (kolasi: utf8mb4_general_ci)
   
5. Setelah masuk ke database `satria_se2026`:
   - Klik tab **"Import"** di menu atas
   - Klik tombol **"Choose File"**
   - Pilih file: `satria_se2026 (1).sql`
   - Scroll ke bawah, klik tombol **"Go"** atau **"Import"**
   
6. Tunggu proses import selesai (file 18 MB mungkin butuh 1-2 menit)
7. Selesai! Database sudah terisi dengan data lengkap

**CATATAN PENTING untuk file besar:**
- Jika muncul error "file too large", edit file `php.ini` di XAMPP
- Cari baris: `upload_max_filesize = 2M` dan ubah jadi `upload_max_filesize = 50M`
- Cari baris: `post_max_size = 8M` dan ubah jadi `post_max_size = 50M`
- Cari baris: `max_execution_time = 30` dan ubah jadi `max_execution_time = 300`
- Restart Apache di XAMPP Control Panel

## Cara 2: Via Command Line MySQL (Otomatis)

Jalankan file batch yang sudah disediakan:
1. Double-klik file: `Import_Database_Lengkap.bat`
2. Tunggu hingga muncul pesan "Database berhasil di-import!"
3. Tekan sembarang tombol untuk keluar

## Cara 3: Via Python Script (Otomatis dari Aplikasi)

Jalankan file Python yang sudah disediakan:
```
python import_database_lengkap.py
```

## Verifikasi Import Berhasil

Setelah import, cek di phpMyAdmin:
- Database `satria_se2026` harus punya banyak tabel
- Tabel `se_news` harus punya banyak data (ribuan baris)
- Tabel `media_massa_news` juga harus terisi
- Tabel `users` harus ada (untuk login aplikasi)

Jika semua tabel terisi, aplikasi SATRIA SE2026 siap digunakan!
