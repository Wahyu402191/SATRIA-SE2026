-- ═══════════════════════════════════════════════════════════════════════════
-- SATRIA SE2026 — Database Schema
-- Sistem Scraping & Analisis Sentimen Komentar YouTube
-- Badan Pusat Statistik Kabupaten Bangkalan
-- ═══════════════════════════════════════════════════════════════════════════

-- Drop database if exists (CAUTION: This will delete all data!)
-- DROP DATABASE IF EXISTS satria_se2026;

-- Create database
CREATE DATABASE IF NOT EXISTS satria_se2026
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE satria_se2026;

-- ───────────────────────────────────────────────────────────────────────────
-- Table: videos
-- Menyimpan informasi video YouTube yang di-scrape
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(500),
    channel VARCHAR(255),
    views BIGINT DEFAULT 0,
    likes BIGINT DEFAULT 0,
    comment_count BIGINT DEFAULT 0,
    url TEXT,
    thumbnail_url TEXT,
    published_at DATETIME,
    scraped_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_video_id (video_id),
    INDEX idx_scraped_at (scraped_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ───────────────────────────────────────────────────────────────────────────
-- Table: scraping_sessions
-- Menyimpan setiap sesi scraping (satu video bisa di-scrape berkali-kali)
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scraping_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id VARCHAR(50) NOT NULL,
    requested_comments INT DEFAULT 0,
    actual_comments INT DEFAULT 0,
    include_replies BOOLEAN DEFAULT FALSE,
    saved_filename VARCHAR(255),
    scraped_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    INDEX idx_video_id (video_id),
    INDEX idx_scraped_at (scraped_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ───────────────────────────────────────────────────────────────────────────
-- Table: comments
-- Menyimpan komentar individual dari setiap video
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    video_id VARCHAR(50) NOT NULL,
    comment_id VARCHAR(100) NOT NULL UNIQUE,
    author VARCHAR(255),
    text TEXT,
    likes INT DEFAULT 0,
    published_at DATETIME,
    is_reply BOOLEAN DEFAULT FALSE,
    parent_comment_id VARCHAR(100),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES scraping_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_video_id (video_id),
    INDEX idx_comment_id (comment_id),
    INDEX idx_published_at (published_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ───────────────────────────────────────────────────────────────────────────
-- Table: analysis_methods
-- Daftar metode analisis sentimen yang tersedia
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analysis_methods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    method_code VARCHAR(50) NOT NULL UNIQUE,
    method_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_method_code (method_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default methods
INSERT INTO analysis_methods (method_code, method_name, description) VALUES
('naive_bayes', 'Naive Bayes', 'Metode klasifikasi probabilistik berbasis Teorema Bayes'),
('svm', 'Support Vector Machine', 'Metode klasifikasi dengan hyperplane optimal'),
('lstm', 'Long Short-Term Memory', 'Deep Learning dengan arsitektur RNN untuk sequence data'),
('indobert', 'IndoBERT', 'Pre-trained Transformer model untuk bahasa Indonesia')
ON DUPLICATE KEY UPDATE method_name = VALUES(method_name);

-- ───────────────────────────────────────────────────────────────────────────
-- Table: analysis_results
-- Menyimpan hasil analisis sentimen untuk setiap komentar per metode
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analysis_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    comment_id INT NOT NULL,
    method_code VARCHAR(50) NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    score DECIMAL(5, 4),
    preprocessed_text TEXT,
    analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES scraping_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    FOREIGN KEY (method_code) REFERENCES analysis_methods(method_code),
    INDEX idx_session_id (session_id),
    INDEX idx_comment_id (comment_id),
    INDEX idx_method_code (method_code),
    INDEX idx_sentiment (sentiment),
    INDEX idx_analyzed_at (analyzed_at),
    UNIQUE KEY unique_analysis (comment_id, method_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ───────────────────────────────────────────────────────────────────────────
-- Table: analysis_summary
-- Menyimpan ringkasan statistik analisis per session dan metode
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analysis_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    method_code VARCHAR(50) NOT NULL,
    total_comments INT DEFAULT 0,
    positive_count INT DEFAULT 0,
    negative_count INT DEFAULT 0,
    neutral_count INT DEFAULT 0,
    positive_percentage DECIMAL(5, 2),
    negative_percentage DECIMAL(5, 2),
    neutral_percentage DECIMAL(5, 2),
    agreement_rate DECIMAL(5, 2),
    analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES scraping_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (method_code) REFERENCES analysis_methods(method_code),
    INDEX idx_session_id (session_id),
    INDEX idx_method_code (method_code),
    UNIQUE KEY unique_summary (session_id, method_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ───────────────────────────────────────────────────────────────────────────
-- Table: wordcloud_data
-- Menyimpan data untuk wordcloud (top words per sentiment)
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wordcloud_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    word VARCHAR(100) NOT NULL,
    frequency INT DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES scraping_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_sentiment (sentiment),
    INDEX idx_frequency (frequency DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ───────────────────────────────────────────────────────────────────────────
-- Views untuk Dashboard Statistics
-- ───────────────────────────────────────────────────────────────────────────

-- View: Total statistics across all sessions
CREATE OR REPLACE VIEW dashboard_stats AS
SELECT
    COUNT(DISTINCT v.id) as total_videos,
    COUNT(DISTINCT s.id) as total_sessions,
    COALESCE(SUM(s.actual_comments), 0) as total_comments,
    COALESCE(SUM(CASE WHEN ar.sentiment = 'Positif' THEN 1 ELSE 0 END), 0) as total_positive,
    COALESCE(SUM(CASE WHEN ar.sentiment = 'Negatif' THEN 1 ELSE 0 END), 0) as total_negative,
    COALESCE(SUM(CASE WHEN ar.sentiment = 'Netral' THEN 1 ELSE 0 END), 0) as total_neutral
FROM videos v
LEFT JOIN scraping_sessions s ON v.video_id = s.video_id
LEFT JOIN analysis_results ar ON s.id = ar.session_id
WHERE ar.method_code = 'naive_bayes' OR ar.method_code IS NULL;

-- View: Recent activity (last 10 sessions)
CREATE OR REPLACE VIEW recent_activity AS
SELECT
    s.id as session_id,
    v.video_id,
    v.title as video_title,
    v.channel,
    s.actual_comments as comment_count,
    s.scraped_at,
    (SELECT COUNT(DISTINCT ar.id) FROM analysis_results ar WHERE ar.session_id = s.id) as has_analysis
FROM scraping_sessions s
JOIN videos v ON s.video_id = v.video_id
ORDER BY s.scraped_at DESC
LIMIT 10;

-- ═══════════════════════════════════════════════════════════════════════════
-- End of Schema
-- ═══════════════════════════════════════════════════════════════════════════
