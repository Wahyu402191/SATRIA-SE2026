"""
SATRIA SE2026 — Data Storage Layer (MySQL Database)
Badan Pusat Statistik Kabupaten Bangkalan

Refactored to use MySQL instead of JSON files
"""

import json
import os
from datetime import datetime
from db_config import execute_query, execute_many, get_connection
from mysql.connector import Error


class DataStorage:
    def __init__(self, storage_dir='data'):
        """
        Initialize data storage with MySQL database
        Legacy JSON storage_dir kept for backup/migration purposes
        """
        self.storage_dir = storage_dir
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        
        # Test database connection
        try:
            from db_config import test_connection, check_database_exists, ensure_analysis_results_history_schema
            if not test_connection():
                print("[!] Warning: MySQL not connected. Using fallback JSON mode.")
                self.use_mysql = False
            elif not check_database_exists():
                print("[!] Warning: Database tables missing. Using fallback JSON mode.")
                self.use_mysql = False
            else:
                ensure_analysis_results_history_schema()
                self.use_mysql = True
                print("[✓] DataStorage initialized with MySQL backend")
        except Exception as e:
            print(f"[!] MySQL initialization failed: {e}. Using JSON fallback.")
            self.use_mysql = False
    
    def save_comments(self, video_id, video_info, comments, video_url='', include_replies=False, requested_comments=0):
        """
        Save scraped comments to MySQL database
        Returns: video_id (string) for consistency with old API
        """
        if not self.use_mysql:
            return self._save_comments_json(video_id, video_info, comments)
        
        try:
            timestamp = datetime.now()
            
            # ── Insert or Update Video Record ─────────────────────────────
            published_at = None
            if video_info.get('published_at'):
                try:
                    published_at = datetime.fromisoformat(
                        video_info['published_at'].replace('Z', '+00:00')
                    )
                except Exception:
                    published_at = None

            video_query = """
                INSERT INTO videos
                (video_id, video_url, title, channel, views, likes, total_comments,
                 scraped_at, include_replies, requested_comments, available_comments, published_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    scraped_at = VALUES(scraped_at),
                    total_comments = total_comments + VALUES(total_comments),
                    published_at = COALESCE(VALUES(published_at), published_at)
            """

            video_params = (
                video_id,
                video_url or f'https://www.youtube.com/watch?v={video_id}',
                video_info.get('title', 'Unknown'),
                video_info.get('channel', 'Unknown'),
                int(video_info.get('views', 0)),
                int(video_info.get('likes', 0)),
                len(comments),
                timestamp,
                include_replies,
                requested_comments or len(comments),
                int(video_info.get('comments', len(comments))),
                published_at,
            )
            
            execute_query(video_query, video_params)
            
            # ── Batch Insert Comments ──────────────────────────────────────
            if comments:
                comment_query = """
                    INSERT IGNORE INTO comments 
                    (video_id, comment_id, author, text, likes, published_at, is_reply, parent_comment_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                comment_data = []
                for c in comments:
                    # Parse published_at
                    pub_at = None
                    if c.get('published_at'):
                        try:
                            pub_at = datetime.fromisoformat(c['published_at'].replace('Z', '+00:00'))
                        except:
                            pub_at = timestamp
                    
                    comment_data.append((
                        video_id,
                        c.get('comment_id', f"{video_id}_{len(comment_data)}"),
                        c.get('author', 'Unknown'),
                        c.get('text', ''),
                        int(c.get('likes', 0)),
                        pub_at,
                        c.get('is_reply', False),
                        c.get('parent_id')
                    ))
                
                # Batch insert (faster)
                if comment_data:
                    execute_many(comment_query, comment_data)
            
            print(f"[✓] Saved {len(comments)} comments to database for video {video_id}")
            
            # Also save backup JSON file
            self._save_comments_json(video_id, video_info, comments)
            
            return video_id
            
        except Exception as e:
            print(f"[✗] Error saving to database: {e}")
            # Fallback to JSON
            return self._save_comments_json(video_id, video_info, comments)
    
    def _save_comments_json(self, video_id, video_info, comments):
        """Legacy JSON storage (backup/fallback)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{video_id}_{timestamp}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        data = {
            'video_id': video_id,
            'video_info': video_info,
            'comments': comments,
            'total_comments': len(comments),
            'scraped_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def get_saved_files(self):
        """
        Get list of all saved videos from database
        Returns same format as old JSON API for compatibility
        """
        if not self.use_mysql:
            return self._get_saved_files_json()
        
        try:
            query = """
                SELECT 
                    video_id,
                    title,
                    scraped_at,
                    (SELECT COUNT(*) FROM comments WHERE comments.video_id = videos.video_id) as comment_count
                FROM videos
                ORDER BY scraped_at DESC
            """
            
            results = execute_query(query, fetch=True)
            
            files = []
            for row in results:
                files.append({
                    'filename': row['video_id'],  # Use video_id as identifier
                    'video_id': row['video_id'],
                    'video_title': row['title'],
                    'total_comments': row['comment_count'],
                    'scraped_at': row['scraped_at'].isoformat() if row['scraped_at'] else 'Unknown'
                })
            
            return files
            
        except Exception as e:
            print(f"[✗] Error loading saved files from database: {e}")
            return self._get_saved_files_json()
    
    def _get_saved_files_json(self):
        """Legacy JSON file listing"""
        files = []
        if not os.path.exists(self.storage_dir):
            try:
                os.makedirs(self.storage_dir)
            except Exception as e:
                print(f"Error creating storage directory: {e}")
                return files
        
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.storage_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            files.append({
                                'filename': filename,
                                'video_id': data.get('video_id', 'Unknown'),
                                'video_title': data.get('video_info', {}).get('title', 'Unknown'),
                                'total_comments': data.get('total_comments', 0),
                                'scraped_at': data.get('scraped_at', 'Unknown')
                            })
                    except Exception as e:
                        print(f"Error reading file {filename}: {e}")
                        continue
            
            files.sort(key=lambda x: x['scraped_at'], reverse=True)
        except Exception as e:
            print(f"Error listing files: {e}")
        
        return files
    
    def load_comments(self, identifier):
        """
        Load comments by video_id (identifier can be video_id or legacy filename)
        """
        if not self.use_mysql:
            return self._load_comments_json(identifier)
        
        try:
            # Extract video_id from identifier (could be filename or video_id)
            video_id = identifier.split('_')[0] if '_' in identifier else identifier
            
            # Get video info
            video_query = "SELECT * FROM videos WHERE video_id = %s"
            video_result = execute_query(video_query, (video_id,), fetch=True)
            
            if not video_result:
                # Fallback to JSON
                return self._load_comments_json(identifier)
            
            video_info = video_result[0]
            
            # Get comments
            comments_query = """
                SELECT comment_id, author, text, likes, published_at, is_reply, parent_comment_id
                FROM comments
                WHERE video_id = %s
                ORDER BY published_at DESC
            """
            comments_result = execute_query(comments_query, (video_id,), fetch=True)
            
            # Format response to match old JSON structure
            comments = []
            for c in comments_result:
                comments.append({
                    'comment_id': c['comment_id'],
                    'author': c['author'],
                    'text': c['text'],
                    'likes': c['likes'],
                    'published_at': c['published_at'].isoformat() if c['published_at'] else '',
                    'is_reply': bool(c['is_reply']),
                    'parent_id': c['parent_comment_id']
                })
            
            return {
                'video_id': video_info['video_id'],
                'video_info': {
                    'title': video_info['title'],
                    'channel': video_info['channel'],
                    'views': video_info['views'],
                    'likes': video_info['likes'],
                    'comments': video_info['total_comments'],
                    'published_at': video_info['published_at'].isoformat() if video_info.get('published_at') else None
                },
                'comments': comments,
                'total_comments': len(comments),
                'scraped_at': video_info['scraped_at'].isoformat() if video_info['scraped_at'] else ''
            }
            
        except Exception as e:
            print(f"[✗] Error loading comments from database: {e}")
            return self._load_comments_json(identifier)
    
    def _load_comments_json(self, filename):
        """Legacy JSON loading"""
        filepath = os.path.join(self.storage_dir, filename)
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def delete_file(self, identifier):
        """
        Delete a saved video and all related data
        """
        if not self.use_mysql:
            return self._delete_file_json(identifier)
        
        try:
            # Extract video_id
            video_id = identifier.split('_')[0] if '_' in identifier else identifier
            
            # Delete from database (CASCADE will handle comments and analysis)
            query = "DELETE FROM videos WHERE video_id = %s"
            rows = execute_query(query, (video_id,))
            
            # Also delete JSON backup if exists
            self._delete_file_json(identifier)
            
            return rows > 0
            
        except Exception as e:
            print(f"[✗] Error deleting from database: {e}")
            return self._delete_file_json(identifier)
    
    def _delete_file_json(self, filename):
        """Legacy JSON deletion"""
        filepath = os.path.join(self.storage_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    
    def save_analysis_results(self, video_id, comments_with_sentiments, methods_used):
        """
        Save analysis results to database
        
        Args:
            video_id: YouTube video ID
            comments_with_sentiments: List of comment dicts with sentiment fields
            methods_used: List of method names used ['naive_bayes', 'svm', etc.]
        """
        if not self.use_mysql:
            print("[!] MySQL not available, skipping analysis save")
            return
        
        try:
            timestamp = datetime.now()
            
            # ── Create Analysis Session ────────────────────────────────────
            session_query = """
                INSERT INTO analysis_sessions 
                (video_id, methods_used, total_comments_analyzed, started_at, completed_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            session_id = execute_query(session_query, (
                video_id,
                ','.join(methods_used),
                len(comments_with_sentiments),
                timestamp,
                timestamp
            ))
            
            # ── Save Individual Analysis Results ───────────────────────────
            results_query = """
                INSERT INTO analysis_results 
                (analysis_session_id, comment_id, video_id, method_name, sentiment, confidence_score, analyzed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            results_data = []
            for comment in comments_with_sentiments:
                comment_id = comment.get('comment_id', f"{video_id}_{comment.get('text', '')[:20]}")
                
                # Save results for each method
                for method in methods_used:
                    sentiment_key = f"{method}_sentiment"
                    score_key = f"{method}_score"
                    
                    if sentiment_key in comment:
                        results_data.append((
                            session_id,
                            comment_id,
                            video_id,
                            method,
                            comment[sentiment_key],
                            float(comment.get(score_key, 0.0)),
                            timestamp
                        ))
            
            if results_data:
                execute_many(results_query, results_data)
                print(f"[✓] Saved {len(results_data)} analysis results to database")
            
        except Exception as e:
            print(f"[✗] Error saving analysis results: {e}")
