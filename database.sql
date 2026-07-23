-- ═══════════════════════════════════════════════════════════════════════════
-- SATRIA SE2026 — Database Schema (CLEAN VERSION - NO ERRORS)
-- Badan Pusat Statistik Kabupaten Bangkalan
-- ═══════════════════════════════════════════════════════════════════════════

-- Drop database if exists and create new one
DROP DATABASE IF EXISTS satria_se2026;
CREATE DATABASE satria_se2026 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE satria_se2026;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: users
-- Akun login aplikasi (register/login/profil). Dibuat otomatis oleh
-- auth_storage.py (CREATE TABLE IF NOT EXISTS) saat app pertama kali start,
-- didefinisikan di sini juga supaya skema database.sql tetap lengkap untuk
-- instalasi baru.
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    instansi        VARCHAR(255) NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at   DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: videos
-- Menyimpan informasi video YouTube yang di-scrape
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id VARCHAR(20) NOT NULL UNIQUE,
    video_url VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    channel VARCHAR(255),
    views BIGINT DEFAULT 0,
    likes BIGINT DEFAULT 0,
    total_comments INT DEFAULT 0,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    include_replies BOOLEAN DEFAULT FALSE,
    requested_comments INT DEFAULT 0,
    available_comments INT DEFAULT 0,
    published_at DATETIME NULL,
    INDEX idx_video_id (video_id),
    INDEX idx_scraped_at (scraped_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: comments
-- Menyimpan komentar dari video YouTube
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id VARCHAR(20) NOT NULL,
    comment_id VARCHAR(50) NOT NULL UNIQUE,
    author VARCHAR(255),
    text TEXT NOT NULL,
    likes INT DEFAULT 0,
    published_at DATETIME,
    is_reply BOOLEAN DEFAULT FALSE,
    parent_comment_id VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_video_id (video_id),
    INDEX idx_comment_id (comment_id),
    INDEX idx_published_at (published_at),
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: analysis_sessions
-- Menyimpan metadata session analisis (untuk tracking)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE analysis_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id VARCHAR(20) NOT NULL,
    methods_used VARCHAR(255),
    total_comments_analyzed INT DEFAULT 0,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    duration_seconds INT DEFAULT 0,
    INDEX idx_video_id (video_id),
    INDEX idx_started_at (started_at),
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: analysis_results
-- Menyimpan hasil analisis sentimen per komentar
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE analysis_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    analysis_session_id INT NULL,
    comment_id VARCHAR(50) NOT NULL,
    video_id VARCHAR(20) NOT NULL,
    method_name VARCHAR(50) NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(5,4) DEFAULT 0.0000,
    analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_analysis_session_id (analysis_session_id),
    INDEX idx_comment_id (comment_id),
    INDEX idx_video_id (video_id),
    INDEX idx_method (method_name),
    INDEX idx_sentiment (sentiment),
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_session_id) REFERENCES analysis_sessions(id) ON DELETE SET NULL,
    UNIQUE KEY unique_analysis_session (analysis_session_id, comment_id, method_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- MEDIA MASSA TABLES
-- Tabel untuk dashboard Analisis Sentimen Media Massa
-- ═══════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: news_sources
-- Menyimpan daftar sumber media massa (CNN, Kompas, CNBC, Detik, dll)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE news_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    website_url VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source_name (source_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: news_articles
-- Menyimpan artikel berita dari berbagai media massa
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE news_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(1000) NOT NULL,
    content TEXT NOT NULL,
    url VARCHAR(1000),
    source VARCHAR(255) NOT NULL,
    published_date DATETIME,
    month INT NOT NULL,
    year INT NOT NULL,
    imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source (source),
    INDEX idx_month_year (month, year),
    INDEX idx_published_date (published_date),
    FOREIGN KEY (source) REFERENCES news_sources(source_name) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: news_analysis_sessions
-- Menyimpan metadata session analisis untuk media massa
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE news_analysis_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    month INT NOT NULL,
    year INT NOT NULL,
    methods_used VARCHAR(255),
    total_articles_analyzed INT DEFAULT 0,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    duration_seconds INT DEFAULT 0,
    INDEX idx_month_year (month, year),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: news_analysis_results
-- Menyimpan hasil analisis sentimen per artikel berita
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE news_analysis_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    analysis_session_id INT NULL,
    article_id INT NOT NULL,
    method_name VARCHAR(50) NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(5,4) DEFAULT 0.0000,
    analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_analysis_session_id (analysis_session_id),
    INDEX idx_article_id (article_id),
    INDEX idx_method (method_name),
    INDEX idx_sentiment (sentiment),
    FOREIGN KEY (article_id) REFERENCES news_articles(id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_session_id) REFERENCES news_analysis_sessions(id) ON DELETE SET NULL,
    UNIQUE KEY unique_analysis (analysis_session_id, article_id, method_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- SAMPLE DATA untuk testing (opsional)
-- ═══════════════════════════════════════════════════════════════════════════

-- Insert sample news sources
INSERT INTO news_sources (source_name, description, website_url) VALUES
('CNN Indonesia', 'Portal berita CNN Indonesia', 'https://www.cnnindonesia.com'),
('Kompas', 'Media berita Kompas', 'https://www.kompas.com'),
('CNBC Indonesia', 'Portal berita ekonomi dan bisnis', 'https://www.cnbcindonesia.com'),
('Detik', 'Portal berita Detik', 'https://www.detik.com'),
('Tempo', 'Majalah dan portal berita Tempo', 'https://www.tempo.co'),
('Bisnis Indonesia', 'Media berita bisnis dan ekonomi', 'https://www.bisnis.com');

-- ═══════════════════════════════════════════════════════════════════════════
-- BERITA SENSUS EKONOMI 2026 TABLES
-- Tabel untuk dashboard "Berita Sensus Ekonomi 2026" (monitoring otomatis)
-- Terpisah dari news_articles di atas: tabel di atas isinya diimport manual
-- per bulan, sedangkan tabel di bawah ini tumbuh otomatis tiap hari lewat
-- Google News RSS + scraping, jadi butuh kolom pelacakan proses tersendiri.
-- ═══════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: se_news_articles
-- Satu baris per artikel yang ditemukan. Kolom fase-1 (title/url/source/
-- published_date) selalu terisi begitu ditemukan dari RSS. Kolom fase-2
-- (content/scrape_status) diisi belakangan secara best-effort dan TIDAK
-- PERNAH memblokir penghitungan jumlah berita per hari.
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE se_news_articles (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    title                 VARCHAR(1000) NOT NULL,
    url                   VARCHAR(1000) NOT NULL,          -- link RSS asli (kadang redirector Google)
    url_hash              CHAR(40) NOT NULL,                -- SHA1(url) — kunci dedupe (aman utk index)
    resolved_url          VARCHAR(1000) NULL,               -- URL publisher asli hasil resolusi (best-effort)
    source                VARCHAR(255) NULL,                -- nama sumber dari tag <source> RSS
    rss_snippet           TEXT NULL,                         -- ringkasan/description dari RSS, selalu ada
    content               LONGTEXT NULL,                     -- isi artikel hasil scrape, fallback ke rss_snippet
    content_source        ENUM('scraped','rss_snippet','none') NOT NULL DEFAULT 'none',
    scrape_status         ENUM('pending','success','failed') NOT NULL DEFAULT 'pending',
    scrape_attempted_at   DATETIME NULL,
    query_keyword         VARCHAR(255) NULL,                 -- query pencarian yang menemukan artikel ini
    published_date        DATETIME NOT NULL,                 -- waktu terbit (disimpan dalam WIB/Asia-Jakarta)
    published_day         DATE GENERATED ALWAYS AS (DATE(published_date)) STORED,
    discovered_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_url_hash (url_hash),
    INDEX idx_published_day (published_day),
    INDEX idx_source (source),
    INDEX idx_scrape_status (scrape_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: se_news_sentiment
-- Satu baris per (artikel, metode). Sentimen dihitung otomatis begitu artikel
-- ditemukan (4 metode berjalan independen, tanpa training/batch data
-- historis), dan bisa di-refresh ulang lewat halaman Analisis Sentimen
-- (ON DUPLICATE KEY UPDATE menimpa hasil lama).
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE se_news_sentiment (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    article_id        INT NOT NULL,
    method_name       VARCHAR(50) NOT NULL,   -- naive_bayes | svm | lstm | indobert
    sentiment         VARCHAR(20) NOT NULL,   -- Positif | Negatif | Netral
    confidence_score  DECIMAL(6,4) DEFAULT 0.0000,
    analyzed_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES se_news_articles(id) ON DELETE CASCADE,
    UNIQUE KEY uq_article_method (article_id, method_name),
    INDEX idx_method (method_name),
    INDEX idx_sentiment (sentiment)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: se_news_fetch_log
-- Riwayat setiap kali proses fetch (otomatis/manual) berjalan. Dipakai untuk
-- panel status di dashboard, dan sebagai penanda agar scheduler tidak
-- menjalankan fetch dobel dalam interval yang sama (aman meski di-deploy
-- dengan beberapa worker gunicorn sekalipun).
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE se_news_fetch_log (
    id                       INT AUTO_INCREMENT PRIMARY KEY,
    trigger_type             ENUM('scheduler','manual') NOT NULL DEFAULT 'scheduler',
    status                   ENUM('running','success','failed') NOT NULL DEFAULT 'running',
    started_at               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at             DATETIME NULL,
    articles_found           INT DEFAULT 0,
    articles_new             INT DEFAULT 0,
    articles_scraped_ok      INT DEFAULT 0,
    articles_scraped_failed  INT DEFAULT 0,
    error_message            TEXT NULL,
    INDEX idx_started_at (started_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════
-- SELESAI - Database siap digunakan!
-- Total: 12 tabel
-- Auth: users
-- YouTube: videos, comments, analysis_sessions, analysis_results
-- Media Massa: news_sources, news_articles, news_analysis_sessions, news_analysis_results
-- Berita SE2026: se_news_articles, se_news_sentiment, se_news_fetch_log
-- ═══════════════════════════════════════════════════════════════════════════
