"""
SATRIA SE2026 — Media Massa Data Storage Layer (MySQL Database)
Badan Pusat Statistik Kabupaten Bangkalan

Storage handler for news articles from various media sources
"""

import json
import os
from datetime import datetime
from db_config import execute_query, execute_many
import pandas as pd


class MediaMassaStorage:
    def __init__(self, data_dir='data_media_massa'):
        """
        Initialize media massa storage with MySQL database
        data_dir for CSV/Excel imports
        """
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Test database connection
        try:
            from db_config import test_connection, check_database_exists
            if not test_connection():
                print("[!] Warning: MySQL not connected. Using fallback mode.")
                self.use_mysql = False
            elif not check_database_exists():
                print("[!] Warning: Database tables missing. Using fallback mode.")
                self.use_mysql = False
            else:
                self.use_mysql = True
                print("[✓] MediaMassaStorage initialized with MySQL backend")
        except Exception as e:
            print(f"[!] MySQL initialization failed: {e}. Using fallback mode.")
            self.use_mysql = False
    
    def import_news_from_csv(self, csv_path, month, year=2026, source_name='Unknown'):
        """
        Import news articles from CSV file
        Expected columns: title, content, url, published_date, source (optional)
        
        Args:
            csv_path: Path to CSV file
            month: Month number (1-12)
            year: Year (default 2026)
            source_name: Default source name if not in CSV
        
        Returns:
            Number of articles imported
        """
        if not self.use_mysql:
            print("[!] MySQL not available, cannot import")
            return 0
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            # Validate required columns
            required_cols = ['title', 'content']
            if not all(col in df.columns for col in required_cols):
                print(f"[!] CSV must contain columns: {required_cols}")
                return 0
            
            timestamp = datetime.now()
            articles_data = []
            sources_to_add = set()

            def clean(value, default=''):
                """Blank cells come back from pandas as NaN (a float), not a
                missing key — row.get(col, default) doesn't catch that since
                the column exists, it's just empty for this row. An
                unhandled NaN passed to mysql-connector renders as the bare
                word `nan` in the query, which MySQL parses as a column
                reference ('Unknown column nan')."""
                if value is None:
                    return default
                try:
                    if pd.isna(value):
                        return default
                except (TypeError, ValueError):
                    pass
                return value

            for idx, row in df.iterrows():
                # Get source
                source = clean(row.get('source'), source_name)
                sources_to_add.add(source)

                # Parse published date
                pub_date = None
                if 'published_date' in row and pd.notna(row['published_date']):
                    try:
                        pub_date = pd.to_datetime(row['published_date'])
                    except:
                        pub_date = datetime(year, month, 1)
                else:
                    pub_date = datetime(year, month, 1)

                articles_data.append((
                    clean(row['title']),
                    clean(row['content']),
                    clean(row.get('url'), ''),
                    source,
                    pub_date,
                    month,
                    year,
                    timestamp
                ))
            
            # Insert sources first
            source_query = "INSERT IGNORE INTO news_sources (source_name) VALUES (%s)"
            execute_many(source_query, [(s,) for s in sources_to_add])
            
            # Insert articles
            article_query = """
                INSERT INTO news_articles 
                (title, content, url, source, published_date, month, year, imported_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            execute_many(article_query, articles_data)
            
            print(f"[✓] Imported {len(articles_data)} articles from {csv_path}")
            return len(articles_data)
            
        except Exception as e:
            print(f"[✗] Error importing CSV: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def import_news_from_excel(self, excel_path, month, year=2026, source_name='Unknown', sheet_name=0):
        """
        Import news articles from Excel file
        
        Args:
            excel_path: Path to Excel file
            month: Month number (1-12)
            year: Year (default 2026)
            source_name: Default source name if not in Excel
            sheet_name: Sheet name or index (default 0)
        
        Returns:
            Number of articles imported
        """
        if not self.use_mysql:
            print("[!] MySQL not available, cannot import")
            return 0
        
        try:
            # Read Excel
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            # Validate required columns
            required_cols = ['title', 'content']
            if not all(col in df.columns for col in required_cols):
                print(f"[!] Excel must contain columns: {required_cols}")
                return 0
            
            timestamp = datetime.now()
            articles_data = []
            sources_to_add = set()

            def clean(value, default=''):
                """Blank cells come back from pandas as NaN (a float), not a
                missing key — row.get(col, default) doesn't catch that since
                the column exists, it's just empty for this row. An
                unhandled NaN passed to mysql-connector renders as the bare
                word `nan` in the query, which MySQL parses as a column
                reference ('Unknown column nan')."""
                if value is None:
                    return default
                try:
                    if pd.isna(value):
                        return default
                except (TypeError, ValueError):
                    pass
                return value

            for idx, row in df.iterrows():
                # Get source
                source = clean(row.get('source'), source_name)
                sources_to_add.add(source)

                # Parse published date
                pub_date = None
                if 'published_date' in row and pd.notna(row['published_date']):
                    try:
                        pub_date = pd.to_datetime(row['published_date'])
                    except:
                        pub_date = datetime(year, month, 1)
                else:
                    pub_date = datetime(year, month, 1)

                articles_data.append((
                    clean(row['title']),
                    clean(row['content']),
                    clean(row.get('url'), ''),
                    source,
                    pub_date,
                    month,
                    year,
                    timestamp
                ))
            
            # Insert sources first
            source_query = "INSERT IGNORE INTO news_sources (source_name) VALUES (%s)"
            execute_many(source_query, [(s,) for s in sources_to_add])
            
            # Insert articles
            article_query = """
                INSERT INTO news_articles 
                (title, content, url, source, published_date, month, year, imported_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            execute_many(article_query, articles_data)
            
            print(f"[✓] Imported {len(articles_data)} articles from {excel_path}")
            return len(articles_data)
            
        except Exception as e:
            print(f"[✗] Error importing Excel: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def get_available_months(self):
        """
        Get list of months that have news data
        
        Returns:
            List of dicts with month info: [{'value': '2026-01', 'label': 'Januari 2026', 'count': 150}, ...]
        """
        if not self.use_mysql:
            return []
        
        try:
            query = """
                SELECT year, month, COUNT(*) as count
                FROM news_articles
                GROUP BY year, month
                ORDER BY year DESC, month ASC
            """
            
            results = execute_query(query, fetch=True)
            
            month_names = [
                'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
            ]
            
            months = []
            for row in results:
                year = row['year']
                month = row['month']
                count = row['count']
                
                month_label = f"{month_names[month-1]} {year}"
                month_value = f"{year}-{month:02d}"
                
                months.append({
                    'value': month_value,
                    'label': month_label,
                    'count': count
                })
            
            return months
            
        except Exception as e:
            print(f"[✗] Error getting available months: {e}")
            return []
    
    def get_articles_by_month(self, month_value):
        """
        Get all articles for a specific month
        
        Args:
            month_value: Month string in format 'YYYY-MM'
        
        Returns:
            List of article dicts
        """
        if not self.use_mysql:
            return []
        
        try:
            # Parse month_value
            year, month = month_value.split('-')
            year = int(year)
            month = int(month)
            
            query = """
                SELECT id, title, content, url, source, published_date
                FROM news_articles
                WHERE year = %s AND month = %s
                ORDER BY published_date DESC
            """
            
            results = execute_query(query, (year, month), fetch=True)
            
            articles = []
            for row in results:
                articles.append({
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content'],
                    'url': row['url'],
                    'source': row['source'],
                    'published_date': row['published_date'].isoformat() if row['published_date'] else ''
                })
            
            return articles
            
        except Exception as e:
            print(f"[✗] Error getting articles by month: {e}")
            return []
    
    def save_analysis_results(self, month_value, articles_with_sentiments, methods_used):
        """
        Save analysis results to database
        
        Args:
            month_value: Month string 'YYYY-MM'
            articles_with_sentiments: List of article dicts with sentiment fields
            methods_used: List of method names ['naive_bayes', 'svm', etc.]
        """
        if not self.use_mysql:
            print("[!] MySQL not available, skipping analysis save")
            return
        
        try:
            timestamp = datetime.now()
            
            # Parse month
            year, month = month_value.split('-')
            year = int(year)
            month = int(month)
            
            # Create Analysis Session
            session_query = """
                INSERT INTO news_analysis_sessions 
                (month, year, methods_used, total_articles_analyzed, started_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            session_id = execute_query(session_query, (
                month,
                year,
                ','.join(methods_used),
                len(articles_with_sentiments),
                timestamp,
                timestamp
            ))
            
            # Save Individual Analysis Results
            results_query = """
                INSERT INTO news_analysis_results 
                (analysis_session_id, article_id, method_name, sentiment, confidence_score, analyzed_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            results_data = []
            for article in articles_with_sentiments:
                article_id = article.get('id')
                
                if not article_id:
                    continue
                
                # Save results for each method
                for method in methods_used:
                    sentiment_key = f"{method}_sentiment"
                    score_key = f"{method}_score"
                    
                    if sentiment_key in article:
                        results_data.append((
                            session_id,
                            article_id,
                            method,
                            article[sentiment_key],
                            float(article.get(score_key, 0.0)),
                            timestamp
                        ))
            
            if results_data:
                execute_many(results_query, results_data)
                print(f"[✓] Saved {len(results_data)} analysis results to database")
            
        except Exception as e:
            print(f"[✗] Error saving analysis results: {e}")
            import traceback
            traceback.print_exc()
    
    def get_statistics(self):
        """
        Get general statistics for dashboard
        
        Returns:
            Dict with stats: total_articles, total_months, total_sources, total_analyzed
        """
        if not self.use_mysql:
            return {
                'total_articles': 0,
                'total_months': 0,
                'total_sources': 0,
                'total_analyzed': 0
            }
        
        try:
            stats = {}
            
            # Total articles
            result = execute_query("SELECT COUNT(*) as count FROM news_articles", fetch=True)
            stats['total_articles'] = result[0]['count'] if result else 0
            
            # Total months
            result = execute_query(
                "SELECT COUNT(DISTINCT CONCAT(year, '-', LPAD(month, 2, '0'))) as count FROM news_articles",
                fetch=True
            )
            stats['total_months'] = result[0]['count'] if result else 0
            
            # Total sources
            result = execute_query("SELECT COUNT(DISTINCT source) as count FROM news_articles", fetch=True)
            stats['total_sources'] = result[0]['count'] if result else 0
            
            # Total analyzed
            result = execute_query("SELECT COUNT(*) as count FROM news_analysis_sessions", fetch=True)
            stats['total_analyzed'] = result[0]['count'] if result else 0
            
            return stats
            
        except Exception as e:
            print(f"[✗] Error getting statistics: {e}")
            return {
                'total_articles': 0,
                'total_months': 0,
                'total_sources': 0,
                'total_analyzed': 0
            }
