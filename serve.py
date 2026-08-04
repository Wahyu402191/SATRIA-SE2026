"""
SATRIA SE2026 — Production entrypoint
Badan Pusat Statistik Kabupaten Bangkalan

Menjalankan aplikasi lewat Waitress (WSGI server pure-Python, jalan native
di Windows) alih-alih Flask dev server. Import `app` dari app.py tanpa
menjalankan blok `if __name__ == '__main__':`-nya, jadi `python app.py`
untuk development (livereload, auto-reload) tetap tidak berubah — ini cuma
jalur alternatif untuk dipakai staf/IT BPS lewat Jalankan_SATRIA_SE2026.bat.
"""

import os
import socket
import threading
import webbrowser

from waitress import serve

from app import app


def _detect_lan_ip():
    """Trik socket connect UDP ke alamat luar tanpa benar-benar mengirim
    data apa pun — cara standar untuk tahu IP interface LAN yang dipakai
    mesin ini keluar, tanpa perlu user jalankan ipconfig manual."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        s.close()


def main():
    port = int(os.getenv('PORT', 5000))
    lan_ip = _detect_lan_ip()

    print('=' * 60)
    print('  SATRIA SE2026 — Server berjalan')
    print('=' * 60)
    print(f'  Di komputer ini      : http://127.0.0.1:{port}')
    print(f'  Untuk dibagikan ke staf lain (harus 1 jaringan/WiFi kantor):')
    print(f'                         http://{lan_ip}:{port}')
    print('=' * 60)
    print('  JANGAN TUTUP jendela ini selama aplikasi ingin tetap bisa diakses.')
    print('  Tekan CTRL+C untuk menghentikan server.')
    print('=' * 60)

    # Buka browser otomatis di komputer ini saja — murni kenyamanan, kalau
    # gagal (mis. tidak ada browser default terdeteksi) diabaikan saja.
    try:
        threading.Timer(1.5, lambda: webbrowser.open(f'http://127.0.0.1:{port}')).start()
    except Exception:
        pass

    serve(app, host='0.0.0.0', port=port, threads=8)


if __name__ == '__main__':
    main()
