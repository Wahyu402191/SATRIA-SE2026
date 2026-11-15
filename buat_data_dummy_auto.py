"""
Script otomatis untuk membuat data dummy lengkap SATRIA SE2026
Versi tanpa konfirmasi - langsung eksekusi
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import random
import hashlib

# Konfigurasi
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'satria_se2026'
}

# Jumlah data yang akan dibuat
NUM_VIDEOS = 8
COMMENTS_PER_VIDEO = 100
NUM_NEWS = 150
NUM_SE_NEWS = 300

# Template data
YOUTUBE_VIDEO_TITLES = [
    "Sensus Ekonomi 2026 - Penjelasan Lengkap",
    "Cara Mengisi SE2026 dengan Benar",
    "Tutorial Aplikasi SE2026 untuk UMKM",
    "Pentingnya Sensus Ekonomi bagi Indonesia",
    "Tips Sukses Ikut Sensus Ekonomi 2026",
    "BPS Menjelaskan SE2026",
    "Webinar Sosialisasi SE2026",
    "SE2026: Manfaat untuk Pelaku Usaha",
    "Panduan Lengkap Sensus Ekonomi",
    "Tanya Jawab Seputar SE2026"
]

YOUTUBE_CHANNELS = [
    "BPS RI Official", "BPS Jawa Timur", "BPS Bangkalan",
    "Info Statistik Indonesia", "Edukasi BPS"
]

COMMENT_POSITIVE = [
    "Terima kasih atas penjelasannya yang sangat jelas!",
    "Sangat membantu, sekarang saya lebih paham tentang SE2026",
    "Video yang bagus dan informatif",
    "Penjelasan yang mudah dipahami, terima kasih BPS!",
    "Semoga SE2026 sukses dilaksanakan",
    "Mantap, sangat bermanfaat untuk UMKM seperti saya",
    "Alhamdulillah jadi tahu caranya, terima kasih",
    "Informasi yang sangat berguna",
    "Bagus sekali sosialisasinya",
    "Sukses untuk SE2026!"
]

COMMENT_NEGATIVE = [
    "Kok ribet ya prosesnya?",
    "Kurang jelas penjelasannya",
    "Aplikasinya susah diakses",
    "Terlalu banyak pertanyaan yang harus dijawab",
    "Tidak semua orang punya internet untuk isi online",
    "Bingung cara mengisinya",
    "Waktu pengisiannya terlalu singkat",
    "Sistemnya sering error",
    "Perlu penyederhanaan prosedur",
    "Mohon dipermudah untuk usaha kecil"
]

COMMENT_NEUTRAL = [
    "Kapan batas akhir pengisian SE2026?",
    "Apakah wajib untuk semua jenis usaha?",
    "Bagaimana jika saya belum menerima surat?",
    "Berapa lama waktu yang dibutuhkan untuk mengisi?",
    "Apakah ada sanksi jika tidak mengisi?",
    "Dimana saya bisa mendapat bantuan pengisian?",
    "Apakah data kami dijamin kerahasiaannya?",
    "Bagaimana untuk usaha yang baru berdiri?",
    "Apakah bisa diisi secara offline?",
    "Terima kasih atas informasinya"
]

NEWS_SOURCES = [
    ("Kompas.com", "https://kompas.com"),
    ("Detik.com", "https://detik.com"),
    ("Tempo.co", "https://tempo.co"),
    ("Antara News", "https://antaranews.com"),
    ("CNN Indonesia", "https://cnnindonesia.com"),
    ("Tribun News", "https://tribunnews.com"),
    ("Liputan6", "https://liputan6.com"),
    ("Bisnis.com", "https://bisnis.com"),
    ("Kontan.co.id", "https://kontan.co.id"),
    ("Suara.com", "https://suara.com")
]

NEWS_POSITIVE = [
    "BPS: Sensus Ekonomi 2026 Berjalan Lancar di Seluruh Indonesia",
    "Partisipasi UMKM dalam SE2026 Meningkat Signifikan",
    "Digitalisasi SE2026 Permudah Pelaku Usaha Berikan Data",
    "SE2026 Diprediksi Berhasil Capai Target Nasional",
    "Pemerintah Apresiasi Tingginya Partisipasi dalam SE2026"
]

NEWS_NEGATIVE = [
    "Sejumlah Pelaku UMKM Keluhkan Sistem SE2026 yang Rumit",
    "Kendala Teknis Warnai Pelaksanaan Sensus Ekonomi 2026",
    "Partisipasi SE2026 di Beberapa Daerah Masih Rendah",
    "Pelaku Usaha: Waktu Pengisian SE2026 Terlalu Singkat",
    "SE2026 Hadapi Tantangan di Daerah Terpencil"
]

NEWS_NEUTRAL = [
    "BPS Jelaskan Tahapan Pelaksanaan Sensus Ekonomi 2026",
    "Apa Itu Sensus Ekonomi 2026? Berikut Penjelasan Lengkap",
    "Panduan Lengkap Mengikuti Sensus Ekonomi 2026",
    "Ini Jadwal Pelaksanaan SE2026 di Seluruh Indonesia",
    "SE2026: Target, Metode, dan Manfaatnya"
]

def run():
    print("="*70)
    print("  MEMBUAT DATA DUMMY SATRIA SE2026")
    print("="*70)
    print()
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("[1/6] Menambahkan sumber berita...")
        for name, url in NEWS_SOURCES:
            try:
                cursor.execute(
                    "INSERT IGNORE INTO news_sources (name, url, is_active) VALUES (%s, %s, 1)",
                    (name, url)
                )
            except:
                pass
        conn.commit()
        print(f"  [OK] {len(NEWS_SOURCES)} sumber berita")
        
        print(f"\n[2/6] Membuat {NUM_VIDEOS} video YouTube...")
        video_ids = []
        for i in range(NUM_VIDEOS):
            video_id = f"DUMMY_{i+1:03d}_" + hashlib.md5(f"v{i}".encode()).hexdigest()[:8]
            title = random.choice(YOUTUBE_VIDEO_TITLES)
            channel = random.choice(YOUTUBE_CHANNELS)
            views = random.randint(5000, 100000)
            likes = int(views * random.uniform(0.03, 0.08))
            scraped_at = datetime.now() - timedelta(days=random.randint(1, 30))
            
            try:
                cursor.execute("""
                    INSERT INTO videos 
                    (video_id, title, channel, views, likes, comments, video_url, scraped_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (video_id, title, channel, views, likes, COMMENTS_PER_VIDEO,
                      f"https://youtube.com/watch?v={video_id}", scraped_at))
                video_ids.append(video_id)
            except:
                pass
        conn.commit()
        print(f"  [OK] {len(video_ids)} video dibuat")
        
        print(f"\n[3/6] Membuat {NUM_VIDEOS * COMMENTS_PER_VIDEO} komentar...")
        total = 0
        for vid in video_ids:
            for j in range(COMMENTS_PER_VIDEO):
                sent = random.choice(['pos', 'neg', 'neu'])
                if sent == 'pos':
                    text = random.choice(COMMENT_POSITIVE)
                elif sent == 'neg':
                    text = random.choice(COMMENT_NEGATIVE)
                else:
                    text = random.choice(COMMENT_NEUTRAL)
                
                cid = f"CMT_{vid}_{j:04d}"
                author = f"User{random.randint(1, 1000)}"
                likes = random.randint(0, 50)
                pub = datetime.now() - timedelta(days=random.randint(0, 25))
                
                try:
                    cursor.execute("""
                        INSERT INTO comments 
                        (comment_id, video_id, author, text, likes, published_at, is_reply)
                        VALUES (%s, %s, %s, %s, %s, %s, 0)
                    """, (cid, vid, author, text, likes, pub))
                    total += 1
                except:
                    pass
        conn.commit()
        print(f"  [OK] {total} komentar dibuat")
        
        print(f"\n[4/6] Membuat {NUM_NEWS} berita media massa...")
        cursor.execute("SELECT id FROM news_sources")
        src_ids = [r[0] for r in cursor.fetchall()]
        months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni']
        
        for i in range(NUM_NEWS):
            sent = random.choice(['pos', 'neg', 'neu'])
            if sent == 'pos':
                title = random.choice(NEWS_POSITIVE)
            elif sent == 'neg':
                title = random.choice(NEWS_NEGATIVE)
            else:
                title = random.choice(NEWS_NEUTRAL)
            
            content = f"{title}. Pelaksanaan SE2026 terus berlangsung. Data yang dikumpulkan penting untuk kebijakan ekonomi."
            url = f"https://news.example.com/article-{i+1}"
            pub = datetime.now() - timedelta(days=random.randint(1, 150))
            
            try:
                cursor.execute("""
                    INSERT INTO news_articles 
                    (source_id, title, content, url, published_date, month, scraped_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (random.choice(src_ids), title, content, url, pub, random.choice(months), datetime.now()))
            except:
                pass
        conn.commit()
        print(f"  [OK] Berita media massa dibuat")
        
        print(f"\n[5/6] Membuat {NUM_SE_NEWS} berita SE2026 + sentimen...")
        keywords = ['Sensus Ekonomi 2026', 'SE2026', 'BPS', 'UMKM']
        
        for i in range(NUM_SE_NEWS):
            sent = random.choice(['pos', 'neg', 'neu'])
            if sent == 'pos':
                title = random.choice(NEWS_POSITIVE)
                label = 'positif'
                conf = random.uniform(0.75, 0.95)
            elif sent == 'neg':
                title = random.choice(NEWS_NEGATIVE)
                label = 'negatif'
                conf = random.uniform(0.70, 0.90)
            else:
                title = random.choice(NEWS_NEUTRAL)
                label = 'netral'
                conf = random.uniform(0.65, 0.85)
            
            kw = random.choice(keywords)
            src = random.choice([s[0] for s in NEWS_SOURCES])
            pub = datetime.now() - timedelta(days=random.randint(1, 150))
            snippet = f"{title[:80]}..."
            url = f"https://news.google.com/se2026-{i+1}"
            
            try:
                cursor.execute("""
                    INSERT INTO se_news_articles 
                    (keyword, title, link, source, published_date, snippet, fetched_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (kw, title, url, src, pub, snippet, datetime.now()))
                
                aid = cursor.lastrowid
                
                for method in ['naive_bayes', 'svm', 'lstm', 'indobert']:
                    c = conf + random.uniform(-0.05, 0.05)
                    c = max(0.5, min(0.99, c))
                    try:
                        cursor.execute("""
                            INSERT INTO se_news_sentiment 
                            (article_id, method_name, sentiment, confidence_score, analyzed_at)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (aid, method, label, c, datetime.now()))
                    except:
                        pass
            except:
                pass
        conn.commit()
        print(f"  [OK] Berita SE2026 + sentimen dibuat")
        
        print(f"\n[6/6] Membuat user accounts...")
        users = [
            ("Admin SATRIA", "admin@bps.go.id", "BPS Kab. Bangkalan", "admin123"),
            ("Operator SE2026", "operator@bps.go.id", "BPS Kab. Bangkalan", "operator123"),
            ("Demo User", "demo@example.com", "Instansi Demo", "demo123"),
        ]
        
        for name, email, inst, pwd in users:
            phash = hashlib.sha256(pwd.encode()).hexdigest()
            try:
                cursor.execute("""
                    INSERT INTO users (name, email, instansi, password, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name)
                """, (name, email, inst, phash, datetime.now()))
            except:
                pass
        conn.commit()
        print(f"  [OK] 3 user dibuat")
        
        # Log
        for kw in keywords:
            try:
                cursor.execute("""
                    INSERT INTO se_news_fetch_log 
                    (keyword, articles_count, fetched_at, status)
                    VALUES (%s, %s, %s, 'success')
                """, (kw, random.randint(40, 80), datetime.now()))
            except:
                pass
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("  SELESAI!")
        print("="*70)
        print("\nData dummy berhasil dibuat:")
        print(f"  - Video YouTube: {NUM_VIDEOS}")
        print(f"  - Komentar: {NUM_VIDEOS * COMMENTS_PER_VIDEO}")
        print(f"  - Berita Media Massa: {NUM_NEWS}")
        print(f"  - Berita SE2026: {NUM_SE_NEWS} (dengan sentimen)")
        print(f"  - User Accounts: 3")
        print("\nLogin credentials:")
        print("  admin@bps.go.id / admin123")
        print("  operator@bps.go.id / operator123")
        print("  demo@example.com / demo123")
        print("\nRESTART aplikasi untuk melihat data!")
        print("="*70)
        
    except Error as e:
        print(f"\n[ERROR] {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        if run():
            print("\n[INFO] Silakan restart aplikasi sekarang")
        input("\nTekan Enter untuk keluar...")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("\nTekan Enter untuk keluar...")
