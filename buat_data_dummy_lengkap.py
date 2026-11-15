"""
Script untuk membuat data dummy lengkap untuk semua fitur SATRIA SE2026
- YouTube: Video, Komentar, Analisis
- Media Massa: Berita dari berbagai sumber
- Berita SE2026: Artikel Sensus Ekonomi 2026
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import random
import hashlib

# Konfigurasi database
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'satria_se2026'
}

# Data dummy untuk generate konten
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
    "BPS RI Official",
    "BPS Jawa Timur",
    "BPS Bangkalan",
    "Info Statistik Indonesia",
    "Edukasi BPS"
]

COMMENT_TEMPLATES_POSITIVE = [
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

COMMENT_TEMPLATES_NEGATIVE = [
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

COMMENT_TEMPLATES_NEUTRAL = [
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

NEWS_TITLES_POSITIVE = [
    "BPS: Sensus Ekonomi 2026 Berjalan Lancar di Seluruh Indonesia",
    "Partisipasi UMKM dalam SE2026 Meningkat Signifikan",
    "Digitalisasi SE2026 Permudah Pelaku Usaha Berikan Data",
    "SE2026 Diprediksi Berhasil Capai Target Nasional",
    "Pemerintah Apresiasi Tingginya Partisipasi dalam SE2026",
    "Data SE2026 akan Jadi Acuan Kebijakan Ekonomi Nasional",
    "SE2026: Langkah Maju Pendataan Ekonomi Indonesia",
    "Keberhasilan SE2026 Bukti Komitmen Pelaku Usaha",
    "BPS Optimis SE2026 Lampaui Target",
    "Sensus Ekonomi 2026 Raih Respon Positif Masyarakat"
]

NEWS_TITLES_NEGATIVE = [
    "Sejumlah Pelaku UMKM Keluhkan Sistem SE2026 yang Rumit",
    "Kendala Teknis Warnai Pelaksanaan Sensus Ekonomi 2026",
    "Partisipasi SE2026 di Beberapa Daerah Masih Rendah",
    "Pelaku Usaha: Waktu Pengisian SE2026 Terlalu Singkat",
    "SE2026 Hadapi Tantangan di Daerah Terpencil",
    "Sistem Online SE2026 Kerap Alami Gangguan",
    "Sosialisasi SE2026 Dinilai Belum Maksimal",
    "UMKM Minta Perpanjangan Waktu Pengisian SE2026",
    "Akses Internet Jadi Hambatan Pelaksanaan SE2026",
    "Kritik untuk Pelaksanaan Sensus Ekonomi 2026"
]

NEWS_TITLES_NEUTRAL = [
    "BPS Jelaskan Tahapan Pelaksanaan Sensus Ekonomi 2026",
    "Apa Itu Sensus Ekonomi 2026? Berikut Penjelasan Lengkap",
    "Panduan Lengkap Mengikuti Sensus Ekonomi 2026",
    "Ini Jadwal Pelaksanaan SE2026 di Seluruh Indonesia",
    "SE2026: Target, Metode, dan Manfaatnya",
    "Fakta Menarik Seputar Sensus Ekonomi 2026",
    "Siapa Saja yang Wajib Ikut SE2026?",
    "Tanya Jawab Seputar Sensus Ekonomi 2026",
    "Perbedaan SE2026 dengan Sensus Sebelumnya",
    "Data Apa Saja yang Dikumpulkan dalam SE2026?"
]

def create_connection():
    """Buat koneksi ke database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[ERROR] Koneksi gagal: {e}")
        return None

def clear_existing_data(cursor):
    """Hapus data dummy yang sudah ada (opsional)"""
    print("\n[INFO] Menghapus data lama...")
    tables = [
        'analysis_results',
        'comments',
        'analysis_sessions',
        'videos',
        'news_analysis_results',
        'news_analysis_sessions',
        'news_articles',
        'se_news_sentiment',
        'se_news_articles'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM `{table}`")
            print(f"  - Tabel {table} dikosongkan")
        except Error as e:
            print(f"  - Skip {table}: {e}")

def insert_news_sources(cursor):
    """Insert sumber berita jika belum ada"""
    print("\n[1/6] Menambahkan sumber berita...")
    
    for name, url in NEWS_SOURCES:
        try:
            cursor.execute(
                "INSERT IGNORE INTO news_sources (name, url, is_active) VALUES (%s, %s, 1)",
                (name, url)
            )
        except Error:
            pass
    
    print(f"  [OK] {len(NEWS_SOURCES)} sumber berita siap")

def insert_youtube_dummy_data(cursor, num_videos=5, comments_per_video=50):
    """Insert data dummy untuk YouTube"""
    print(f"\n[2/6] Membuat data YouTube dummy...")
    print(f"  - {num_videos} video")
    print(f"  - {comments_per_video} komentar per video")
    
    video_ids = []
    
    # Insert videos
    for i in range(num_videos):
        video_id = f"DUMMY_{i+1:03d}_" + hashlib.md5(f"video{i}".encode()).hexdigest()[:8]
        title = random.choice(YOUTUBE_VIDEO_TITLES)
        channel = random.choice(YOUTUBE_CHANNELS)
        
        views = random.randint(1000, 100000)
        likes = int(views * random.uniform(0.02, 0.10))
        comments_count = comments_per_video
        
        scraped_at = datetime.now() - timedelta(days=random.randint(1, 30))
        
        try:
            cursor.execute("""
                INSERT INTO videos 
                (video_id, title, channel, views, likes, comments, video_url, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                video_id, title, channel, views, likes, comments_count,
                f"https://youtube.com/watch?v={video_id}", scraped_at
            ))
            video_ids.append(video_id)
            print(f"  [OK] Video {i+1}: {title[:50]}...")
        except Error as e:
            print(f"  [ERROR] Video {i+1}: {e}")
    
    # Insert comments for each video
    print(f"\n  Membuat komentar...")
    total_comments = 0
    
    for video_id in video_ids:
        for j in range(comments_per_video):
            # Random sentiment
            sentiment_type = random.choice(['positive', 'negative', 'neutral'])
            
            if sentiment_type == 'positive':
                text = random.choice(COMMENT_TEMPLATES_POSITIVE)
                likes = random.randint(0, 50)
            elif sentiment_type == 'negative':
                text = random.choice(COMMENT_TEMPLATES_NEGATIVE)
                likes = random.randint(0, 20)
            else:
                text = random.choice(COMMENT_TEMPLATES_NEUTRAL)
                likes = random.randint(0, 30)
            
            author = f"User{random.randint(1, 1000)}"
            published_at = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            comment_id = f"COMMENT_{video_id}_{j:04d}"
            
            try:
                cursor.execute("""
                    INSERT INTO comments 
                    (comment_id, video_id, author, text, likes, published_at, is_reply)
                    VALUES (%s, %s, %s, %s, %s, %s, 0)
                """, (comment_id, video_id, author, text, likes, published_at))
                total_comments += 1
            except Error as e:
                if 'Duplicate entry' not in str(e):
                    print(f"  [ERROR] Comment: {e}")
    
    print(f"  [OK] {total_comments} komentar dibuat")
    return video_ids

def insert_media_massa_dummy_data(cursor, num_articles=100):
    """Insert data dummy untuk Media Massa"""
    print(f"\n[3/6] Membuat data Media Massa dummy...")
    print(f"  - {num_articles} artikel berita")
    
    # Get source IDs
    cursor.execute("SELECT id FROM news_sources")
    source_ids = [row[0] for row in cursor.fetchall()]
    
    if not source_ids:
        print("  [ERROR] Tidak ada sumber berita!")
        return
    
    months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni']
    
    articles_created = 0
    
    for i in range(num_articles):
        # Random sentiment
        sentiment_type = random.choice(['positive', 'negative', 'neutral'])
        
        if sentiment_type == 'positive':
            title = random.choice(NEWS_TITLES_POSITIVE)
        elif sentiment_type == 'negative':
            title = random.choice(NEWS_TITLES_NEGATIVE)
        else:
            title = random.choice(NEWS_TITLES_NEUTRAL)
        
        source_id = random.choice(source_ids)
        published_date = datetime.now() - timedelta(days=random.randint(1, 180))
        month = random.choice(months)
        
        # Generate konten dummy
        content = f"{title}. Pelaksanaan Sensus Ekonomi 2026 terus berlangsung di seluruh Indonesia. " \
                  f"Badan Pusat Statistik (BPS) mencatat berbagai perkembangan dalam proses pendataan ini. " \
                  f"Data yang dikumpulkan akan menjadi acuan penting untuk kebijakan ekonomi nasional."
        
        url = f"https://example.com/news/se2026-article-{i+1}"
        
        try:
            cursor.execute("""
                INSERT INTO news_articles 
                (source_id, title, content, url, published_date, month, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (source_id, title, content, url, published_date, month, datetime.now()))
            articles_created += 1
        except Error as e:
            if 'Duplicate entry' not in str(e):
                print(f"  [ERROR] Article {i+1}: {e}")
    
    print(f"  [OK] {articles_created} artikel berita dibuat")

def insert_se_news_dummy_data(cursor, num_articles=200):
    """Insert data dummy untuk Berita SE2026 (dari Google News RSS)"""
    print(f"\n[4/6] Membuat data Berita SE2026 dummy...")
    print(f"  - {num_articles} artikel SE2026")
    
    keywords = ['Sensus Ekonomi 2026', 'SE2026', 'BPS', 'UMKM', 'Ekonomi Indonesia']
    
    articles_created = 0
    
    for i in range(num_articles):
        # Random sentiment
        sentiment_type = random.choice(['positive', 'negative', 'neutral'])
        
        if sentiment_type == 'positive':
            title = random.choice(NEWS_TITLES_POSITIVE)
        elif sentiment_type == 'negative':
            title = random.choice(NEWS_TITLES_NEGATIVE)
        else:
            title = random.choice(NEWS_TITLES_NEUTRAL)
        
        keyword = random.choice(keywords)
        source = random.choice([s[0] for s in NEWS_SOURCES])
        
        published_date = datetime.now() - timedelta(days=random.randint(1, 180))
        
        # Generate snippet
        snippet = f"Informasi terbaru seputar {keyword}. {title}. " \
                  f"Artikel lengkap dari {source}."
        
        url = f"https://news.google.com/articles/se2026-{i+1}"
        
        try:
            cursor.execute("""
                INSERT INTO se_news_articles 
                (keyword, title, link, source, published_date, snippet, fetched_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (keyword, title, url, source, published_date, snippet, datetime.now()))
            
            article_id = cursor.lastrowid
            
            # Insert sentiment untuk artikel ini
            methods = ['naive_bayes', 'svm', 'lstm', 'indobert']
            sentiments = {
                'positive': ('positif', random.uniform(0.7, 0.95)),
                'negative': ('negatif', random.uniform(0.65, 0.90)),
                'neutral': ('netral', random.uniform(0.60, 0.85))
            }
            
            sentiment_label, confidence = sentiments[sentiment_type]
            
            for method in methods:
                conf_variation = confidence + random.uniform(-0.05, 0.05)
                conf_variation = max(0.5, min(0.99, conf_variation))
                
                try:
                    cursor.execute("""
                        INSERT INTO se_news_sentiment 
                        (article_id, method_name, sentiment, confidence_score, analyzed_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (article_id, method, sentiment_label, conf_variation, datetime.now()))
                except Error:
                    pass
            
            articles_created += 1
            
        except Error as e:
            if 'Duplicate entry' not in str(e):
                print(f"  [ERROR] SE Article {i+1}: {e}")
    
    print(f"  [OK] {articles_created} artikel SE2026 dibuat dengan sentimen")

def insert_user_dummy(cursor):
    """Insert user dummy untuk login"""
    print(f"\n[5/6] Membuat user dummy...")
    
    users = [
        ("Admin SATRIA", "admin@bps.go.id", "BPS Kabupaten Bangkalan", "admin123"),
        ("Operator SE2026", "operator@bps.go.id", "BPS Kabupaten Bangkalan", "operator123"),
        ("Demo User", "demo@example.com", "Instansi Demo", "demo123"),
    ]
    
    for name, email, instansi, password in users:
        # Hash password (sederhana, di production pakai bcrypt)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            cursor.execute("""
                INSERT INTO users (name, email, instansi, password, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE name=VALUES(name)
            """, (name, email, instansi, password_hash, datetime.now()))
            print(f"  [OK] User: {email} (password: {password})")
        except Error as e:
            print(f"  [ERROR] User {email}: {e}")

def insert_fetch_logs(cursor):
    """Insert log pengambilan berita"""
    print(f"\n[6/6] Membuat log pengambilan berita...")
    
    keywords = ['Sensus Ekonomi 2026', 'SE2026', 'BPS', 'UMKM', 'Ekonomi Indonesia']
    
    for keyword in keywords:
        try:
            cursor.execute("""
                INSERT INTO se_news_fetch_log 
                (keyword, articles_count, fetched_at, status)
                VALUES (%s, %s, %s, 'success')
            """, (keyword, random.randint(30, 50), datetime.now()))
        except Error:
            pass
    
    print(f"  [OK] Log dibuat untuk {len(keywords)} keyword")

def main():
    """Fungsi utama"""
    print("="*70)
    print("  GENERATOR DATA DUMMY SATRIA SE2026")
    print("="*70)
    print("\nScript ini akan membuat data dummy untuk:")
    print("1. YouTube: Video dan Komentar")
    print("2. Media Massa: Artikel Berita")
    print("3. Berita SE2026: Artikel dari Google News")
    print("4. User Accounts untuk Login")
    print()
    
    # Konfirmasi
    confirm = input("Lanjutkan? (y/n): ").lower()
    if confirm != 'y':
        print("Dibatalkan.")
        return
    
    # Konfigurasi jumlah data
    print("\nKonfigurasi jumlah data:")
    try:
        num_videos = int(input("Jumlah video YouTube (default: 5): ") or "5")
        comments_per_video = int(input("Komentar per video (default: 50): ") or "50")
        num_news = int(input("Jumlah berita media massa (default: 100): ") or "100")
        num_se_news = int(input("Jumlah berita SE2026 (default: 200): ") or "200")
    except ValueError:
        print("Input tidak valid, menggunakan nilai default")
        num_videos = 5
        comments_per_video = 50
        num_news = 100
        num_se_news = 200
    
    # Mulai proses
    conn = create_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Opsional: hapus data lama
        clear_old = input("\nHapus data lama? (y/n, default: n): ").lower()
        if clear_old == 'y':
            clear_existing_data(cursor)
            conn.commit()
        
        # Insert data
        insert_news_sources(cursor)
        conn.commit()
        
        insert_youtube_dummy_data(cursor, num_videos, comments_per_video)
        conn.commit()
        
        insert_media_massa_dummy_data(cursor, num_news)
        conn.commit()
        
        insert_se_news_dummy_data(cursor, num_se_news)
        conn.commit()
        
        insert_user_dummy(cursor)
        conn.commit()
        
        insert_fetch_logs(cursor)
        conn.commit()
        
        print("\n" + "="*70)
        print("  SELESAI!")
        print("="*70)
        print("\n[OK] Data dummy berhasil dibuat!")
        print("\nStatistik:")
        print(f"  - Video YouTube: {num_videos}")
        print(f"  - Komentar: {num_videos * comments_per_video}")
        print(f"  - Berita Media Massa: {num_news}")
        print(f"  - Berita SE2026: {num_se_news}")
        print(f"  - User Accounts: 3")
        print("\nUser untuk login:")
        print("  Email: admin@bps.go.id, Password: admin123")
        print("  Email: operator@bps.go.id, Password: operator123")
        print("  Email: demo@example.com, Password: demo123")
        print("\nSilakan restart aplikasi untuk melihat datanya!")
        print("="*70)
        
        cursor.close()
        
    except Error as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}")
        conn.rollback()
    finally:
        if conn.is_connected():
            conn.close()

if __name__ == "__main__":
    try:
        main()
        input("\nTekan Enter untuk keluar...")
    except KeyboardInterrupt:
        print("\n\nDibatalkan oleh user")
    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}")
        import traceback
        traceback.print_exc()
        input("\nTekan Enter untuk keluar...")
