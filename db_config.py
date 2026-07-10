"""
SATRIA SE2026 — MySQL Database Configuration
Badan Pusat Statistik Kabupaten Bangkalan
"""

import os
import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv
import json

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'satria_se2026'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'raise_on_warnings': False
}

# Connection pool untuk performa
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="satria_pool",
        pool_size=5,
        pool_reset_session=True,
        **DB_CONFIG
    )
    print("[✓] MySQL connection pool initialized successfully")
except Error as e:
    print(f"[✗] MySQL connection pool initialization failed: {e}")
    connection_pool = None


def get_connection():
    """Get connection from pool or create new one"""
    try:
        if connection_pool:
            return connection_pool.get_connection()
        else:
            return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"[✗] Database connection error: {e}")
        raise


def test_connection():
    """Test database connection"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE(), VERSION()")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"[✓] Connected to MySQL database: {result[0]} (version {result[1]})")
        return True
    except Error as e:
        print(f"[✗] Database connection test failed: {e}")
        return False


def execute_query(query, params=None, fetch=False):
    """Execute a single query"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.lastrowid or cursor.rowcount
    except Error as e:
        if conn:
            conn.rollback()
        print(f"[✗] Query execution error: {e}")
        print(f"    Query: {query}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def execute_many(query, data_list):
    """Execute query with multiple rows"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, data_list)
        conn.commit()
        return cursor.rowcount
    except Error as e:
        if conn:
            conn.rollback()
        print(f"[✗] Batch execution error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def check_database_exists():
    """Check if database and tables exist"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Only check core tables needed for application
        required_tables = ['videos', 'comments', 'analysis_results']
        missing_tables = [t for t in required_tables if t not in tables]
        
        cursor.close()
        conn.close()
        
        if missing_tables:
            print(f"[!] Missing tables: {', '.join(missing_tables)}")
            print("[!] Please import database.sql file first")
            return False
        
        print(f"[✓] Core tables ready: {', '.join(required_tables)}")
        return True
        
    except Error as e:
        print(f"[✗] Database check error: {e}")
        return False


def ensure_analysis_results_history_schema():
    """Ensure analysis_results stores results per analysis session."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SHOW COLUMNS FROM analysis_results LIKE 'analysis_session_id'")
        has_session_column = len(cursor.fetchall()) > 0

        if not has_session_column:
            cursor.execute(
                "ALTER TABLE analysis_results ADD COLUMN analysis_session_id INT NULL AFTER id"
            )

        cursor.execute("SHOW INDEX FROM analysis_results WHERE Key_name = 'unique_analysis_session'")
        has_new_unique = len(cursor.fetchall()) > 0

        if not has_new_unique:
            cursor.execute("SHOW INDEX FROM analysis_results WHERE Key_name = 'unique_analysis'")
            has_old_unique = len(cursor.fetchall()) > 0

            if has_old_unique:
                cursor.execute("ALTER TABLE analysis_results DROP INDEX unique_analysis")

            cursor.execute(
                """
                ALTER TABLE analysis_results
                ADD UNIQUE KEY unique_analysis_session (analysis_session_id, comment_id, method_name)
                """
            )

        cursor.execute("SHOW INDEX FROM analysis_results WHERE Key_name = 'idx_analysis_session_id'")
        has_session_index = len(cursor.fetchall()) > 0
        if not has_session_index:
            cursor.execute(
                "ALTER TABLE analysis_results ADD INDEX idx_analysis_session_id (analysis_session_id)"
            )

        conn.commit()
        print("[✓] analysis_results history schema verified")
        return True

    except Error as e:
        if conn:
            conn.rollback()
        print(f"[✗] Analysis results schema migration failed: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_latest_analysis_session_id(video_id):
    """Get latest analysis session id for a video, if available."""
    query = """
        SELECT id
        FROM analysis_sessions
        WHERE video_id = %s
        ORDER BY completed_at DESC, id DESC
        LIMIT 1
    """
    result = execute_query(query, (video_id,), fetch=True)
    return result[0]['id'] if result else None


# Test connection on import
if __name__ != '__main__':
    try:
        if test_connection():
            check_database_exists()
    except Exception as e:
        print(f"[!] Warning: Database connection test failed: {e}")


# ══════════════════════════════════════════════════════════════════════════
# Helper Functions for Common Operations
# ══════════════════════════════════════════════════════════════════════════

def get_video_by_id(video_id):
    """Get video data by video_id"""
    query = "SELECT * FROM videos WHERE video_id = %s"
    result = execute_query(query, (video_id,), fetch=True)
    return result[0] if result else None


def get_comments_by_video(video_id, limit=None):
    """Get all comments for a video"""
    query = "SELECT * FROM comments WHERE video_id = %s ORDER BY published_at DESC"
    if limit:
        query += f" LIMIT {limit}"
    return execute_query(query, (video_id,), fetch=True)


def get_analysis_results(video_id, method_name=None):
    """Get analysis results for a video"""
    session_id = get_latest_analysis_session_id(video_id)

    if method_name:
        if session_id:
            query = """
                SELECT c.*, ar.sentiment, ar.confidence_score 
                FROM comments c
                JOIN analysis_results ar ON c.comment_id = ar.comment_id
                WHERE ar.video_id = %s AND ar.method_name = %s AND ar.analysis_session_id = %s
                ORDER BY c.published_at DESC
            """
            return execute_query(query, (video_id, method_name, session_id), fetch=True)

        query = """
            SELECT c.*, ar.sentiment, ar.confidence_score 
            FROM comments c
            JOIN analysis_results ar ON c.comment_id = ar.comment_id
            WHERE ar.video_id = %s AND ar.method_name = %s
            ORDER BY c.published_at DESC
        """
        return execute_query(query, (video_id, method_name), fetch=True)
    else:
        if session_id:
            query = """
                SELECT * FROM analysis_results 
                WHERE video_id = %s AND analysis_session_id = %s
            """
            return execute_query(query, (video_id, session_id), fetch=True)

        query = "SELECT * FROM analysis_results WHERE video_id = %s"
        return execute_query(query, (video_id,), fetch=True)


def get_sentiment_summary(video_id):
    """Get sentiment summary for a video"""
    session_id = get_latest_analysis_session_id(video_id)

    if session_id:
        query = """
            SELECT method_name, sentiment, COUNT(*) as count, 
                   ROUND(AVG(confidence_score), 4) as avg_confidence
            FROM analysis_results
            WHERE video_id = %s AND analysis_session_id = %s
            GROUP BY method_name, sentiment
        """
        return execute_query(query, (video_id, session_id), fetch=True)

    query = """
        SELECT method_name, sentiment, COUNT(*) as count, 
               ROUND(AVG(confidence_score), 4) as avg_confidence
        FROM analysis_results
        WHERE video_id = %s
        GROUP BY method_name, sentiment
    """
    return execute_query(query, (video_id,), fetch=True)


def get_all_videos():
    """Get all scraped videos"""
    query = """
        SELECT v.*, 
               COUNT(DISTINCT c.id) as comment_count,
               COUNT(DISTINCT ar.id) as analyzed_count
        FROM videos v
        LEFT JOIN comments c ON v.video_id = c.video_id
        LEFT JOIN analysis_results ar ON v.video_id = ar.video_id
        GROUP BY v.id
        ORDER BY v.scraped_at DESC
    """
    return execute_query(query, fetch=True)


def delete_video_and_related(video_id):
    """Delete video and all related data (CASCADE will handle it)"""
    query = "DELETE FROM videos WHERE video_id = %s"
    return execute_query(query, (video_id,))
