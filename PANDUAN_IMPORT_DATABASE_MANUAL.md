# Panduan Import Database Manual via phpMyAdmin

## Mengapa Database Kosong?

Aplikasi saat ini menggunakan file `database.sql` yang hanya berisi struktur tabel kosong (19 KB).
File `satria_se2026 (1).sql` adalah database lengkap dengan data (18 MB).

## Cara Import Database Lengkap via phpMyAdmin

### Langkah 1: Buka phpMyAdmin

1. Buka **XAMPP Control Panel**
2. Pastikan **MySQL** sudah running (klik Start jika belum)
3. Klik tombol **Admin** di sebelah MySQL
4. Browser akan membuka phpMyAdmin di: `http://localhost/phpmyadmin`

### Langkah 2: Hapus Database Lama (Jika Ada)

1. Di panel kiri, cari database bernama **`satria_se2026`**
2. Klik database tersebut
3. Klik tab **"Operations"** (di bagian atas)
4. Scroll ke bawah, cari bagian **"Remove database"** atau **"Drop the database"**
5. Klik tombol **"Drop the database (DROP)"**
6. Konfirmasi dengan klik **OK**

### Langkah 3: Buat Database Baru

1. Klik tab **"Databases"** di menu atas
2. Di bagian **"Create database"**:
   - Ketik nama: **`satria_se2026`**
   - Pilih Collation: **`utf8mb4_general_ci`**
3. Klik tombol **"Create"**

### Langkah 4: Import File SQL Lengkap

1. Klik database **`satria_se2026`** yang baru dibuat (di panel kiri)
2. Klik tab **"Import"** di bagian atas
3. Klik tombol **"Choose File"** atau **"Browse..."**
4. Pilih file: **`satria_se2026 (1).sql`** (ada di folder `C:\Users\LAPTOP\SATRIA-SE2026`)
5. **PENTING:** Scroll ke bawah, pastikan format: **SQL**
6. Klik tombol **"Go"** atau **"Import"** di bagian paling bawah

### Langkah 5: Tunggu Proses Import

- File berukuran 18 MB, akan memakan waktu **1-3 menit**
- Jangan tutup browser atau refresh halaman
- Tunggu sampai muncul pesan sukses: **"Import has been successfully finished"**

### Langkah 6: Verifikasi Import Berhasil

Setelah import selesai, cek database:

1. Di panel kiri, klik database **`satria_se2026`**
2. Anda harus melihat banyak tabel, antara lain:
   - `se_news` - Berita Sensus Ekonomi (harus ada ribuan baris data)
   - `media_massa_news` - Berita Media Massa
   - `videos` - Data video YouTube
   - `comments` - Komentar YouTube
   - `users` - Akun pengguna
   - Dan tabel-tabel lainnya

3. Klik salah satu tabel (misal: `se_news`)
4. Klik tab **"Browse"**
5. Jika ada banyak data (ribuan/puluhan ribu baris), berarti **import berhasil!**

## Troubleshooting: Jika Muncul Error "File Too Large"

Jika phpMyAdmin menolak file karena terlalu besar, edit konfigurasi PHP:

1. Buka XAMPP Control Panel
2. Klik tombol **"Config"** di sebelah Apache
3. Pilih **"PHP (php.ini)"**
4. Cari dan ubah baris berikut:
   ```
   upload_max_filesize = 2M      →  upload_max_filesize = 50M
   post_max_size = 8M            →  post_max_size = 50M
   max_execution_time = 30       →  max_execution_time = 300
   max_input_time = 60           →  max_input_time = 300
   ```
5. Save file
6. Di XAMPP Control Panel, klik **Stop** lalu **Start** Apache
7. Ulangi proses import dari Langkah 4

## Troubleshooting: Jika Import Berhenti di Tengah Jalan

Jika import timeout atau error di tengah jalan:

### Opsi 1: Import via Command Line (Lebih Cepat)

1. Buka **Command Prompt** atau **PowerShell**
2. Jalankan perintah berikut:
   ```cmd
   cd C:\Users\LAPTOP\SATRIA-SE2026
   C:\xampp\mysql\bin\mysql.exe -u root satria_se2026 < "satria_se2026 (1).sql"
   ```
3. Tunggu hingga selesai (biasanya lebih cepat dari phpMyAdmin)

### Opsi 2: Jalankan Script Batch yang Sudah Disediakan

1. Buka folder `C:\Users\LAPTOP\SATRIA-SE2026`
2. **Double-klik** file: **`Import_Database_Fresh.bat`**
3. Ketik **Y** lalu Enter
4. Tunggu hingga muncul pesan "IMPORT BERHASIL!"

## Setelah Import Selesai

1. Database sudah terisi lengkap
2. Jalankan aplikasi dengan double-klik: **`Jalankan_SATRIA_SE2026.bat`**
3. Buka browser: `http://127.0.0.1:5000`
4. Login dengan akun yang ada di database
5. Semua fitur aplikasi sudah bisa digunakan dengan data lengkap!

## Catatan Penting

- File **`database.sql`** (19 KB) = struktur kosong (jangan dipakai)
- File **`satria_se2026 (1).sql`** (18 MB) = database lengkap (yang harus dipakai)
- Pastikan import benar-benar selesai sampai 100% sebelum menutup phpMyAdmin
- Jika aplikasi masih menunjukkan data kosong setelah import, restart aplikasi (tutup lalu buka lagi)
