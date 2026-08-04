# Cara Menjalankan SATRIA SE2026

Panduan singkat untuk IT/operator BPS Kabupaten Bangkalan menjalankan aplikasi ini di komputer kantor.

## Prasyarat (sekali di awal)

Komputer yang dipakai sebagai server perlu sudah punya:
- **Python 3.10 atau lebih baru**
- **XAMPP** (atau MySQL/MariaDB lain) dengan database `satria_se2026` sudah ter-import

Kalau memakai komputer yang sama seperti saat pengembangan, kedua hal ini sudah tersedia — tinggal lanjut ke bawah. Kalau pindah ke komputer baru, install dua hal itu dulu sebelum lanjut.

## Menjalankan aplikasi

Cukup **double-klik `Jalankan_SATRIA_SE2026.bat`**. Tidak perlu buka XAMPP Control Panel secara manual — kalau database (MySQL) belum menyala, `.bat` ini otomatis menyalakannya duluan (dari `C:\xampp`) sebelum menjalankan aplikasinya. Kalau MySQL sudah menyala duluan (mis. sudah dibuka lewat XAMPP Control Panel), langkah ini otomatis dilewati.

Apache/PHP/modul XAMPP lain **tidak perlu** dinyalakan — aplikasi ini jalan sendiri lewat servernya sendiri (bukan lewat Apache), cuma butuh MySQL-nya saja.

- Pertama kali dijalankan, akan ada proses "Setup awal" (beberapa menit) untuk menyiapkan komponen aplikasi — ini normal, hanya terjadi sekali.
- Setelah itu, jendela hitam akan menampilkan alamat yang bisa dibuka di browser, contohnya:

  ```
  Di komputer ini      : http://127.0.0.1:5000
  Untuk dibagikan ke staf lain (harus 1 jaringan/WiFi kantor):
                          http://192.168.1.23:5000
  ```

- **Jangan tutup jendela ini** selama aplikasi ingin tetap bisa diakses. Menutup jendela = server berhenti.

## Membagikan ke staf lain

Salin alamat "Untuk dibagikan ke staf lain" dari jendela di atas, kirim ke staf lain (WA/email), suruh mereka **bookmark** alamat itu di browser. Selama komputer server menyala dan `Jalankan_SATRIA_SE2026.bat` masih berjalan, siapa pun di jaringan kantor yang sama bisa membuka alamat itu tanpa install apa pun.

### Supaya PC lain benar-benar bisa akses (Windows Firewall)

Secara default Windows Firewall biasanya memblokir koneksi masuk dari PC lain. Jalankan perintah ini **sekali saja**, di **PowerShell as Administrator** di komputer server:

```powershell
New-NetFirewallRule -DisplayName "SATRIA SE2026" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

## Supaya tidak perlu double-klik setiap hari (opsional)

Kalau mau aplikasi otomatis jalan sendiri setiap komputer dinyalakan/restart (tanpa perlu double-klik `.bat` lagi setiap pagi):

1. Klik kanan `Pasang_Auto-Start.ps1` → **Run with PowerShell**.
2. Pilih **Yes** kalau diminta izin Administrator.
3. Cukup dijalankan **sekali** — setelahnya otomatis jalan tiap komputer menyala.

## Rekomendasi keamanan sebelum dipakai bersama-sama

File `.env` di folder aplikasi ini punya 2 hal yang sebaiknya diperbaiki sebelum diakses banyak orang (bukan cuma di komputer sendiri lagi):

1. **`SECRET_KEY`** masih nilai bawaan (`your-secret-key-change-this-in-production`). Ganti dengan teks acak yang panjang dan rahasia — ini dipakai untuk mengamankan sesi login pengguna.
2. **`MYSQL_PASSWORD`** kosong (akun `root` tanpa kata sandi). Sebaiknya diberi kata sandi, atau dibuatkan akun MySQL khusus untuk aplikasi ini dengan akses terbatas ke database `satria_se2026` saja.

Kedua hal ini sengaja **tidak diubah otomatis** karena menyangkut kredensial yang sedang aktif dipakai — sebaiknya diputuskan dan diubah sendiri oleh yang bertanggung jawab atas komputer/database ini.

## Menghentikan server

Klik jendela hitam yang terbuka, tekan `CTRL+C`, atau tutup jendelanya langsung.
