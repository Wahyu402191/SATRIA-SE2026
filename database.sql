-- ═══════════════════════════════════════════════════════════════════════════
-- SATRIA SE2026 — Database Schema (CLEAN VERSION - NO ERRORS)
-- Badan Pusat Statistik Kabupaten Bangkalan
-- ═══════════════════════════════════════════════════════════════════════════

-- Drop database if exists and create new one
DROP DATABASE IF EXISTS satria_se2026;
CREATE DATABASE satria_se2026 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE satria_se2026;

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
-- SELESAI - Database siap digunakan!
-- Total: 8 tabel
-- YouTube: videos, comments, analysis_sessions, analysis_results
-- Media Massa: news_sources, news_articles, news_analysis_sessions, news_analysis_results
-- ═══════════════════════════════════════════════════════════════════════════
