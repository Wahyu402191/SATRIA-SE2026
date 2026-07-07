import requests
import re
from urllib.parse import urlparse, parse_qs

class YouTubeScraper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://www.googleapis.com/youtube/v3'
    
    def extract_video_id(self, url):
        """
        Extract video ID from various YouTube URL formats
        """
        # Pattern untuk berbagai format URL YouTube
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Jika URL sudah berupa video ID
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url
        
        return None
    
    def get_video_info(self, video_id):
        """
        Get video information
        """
        try:
            url = f"{self.base_url}/videos"
            params = {
                'part': 'snippet,statistics',
                'id': video_id,
                'key': self.api_key
            }
            headers = {
                'Referer': 'http://localhost:5000/'
            }
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get('items'):
                video = data['items'][0]
                return {
                    'title': video['snippet']['title'],
                    'channel': video['snippet']['channelTitle'],
                    'views': video['statistics'].get('viewCount', 0),
                    'likes': video['statistics'].get('likeCount', 0),
                    'comments': video['statistics'].get('commentCount', 0)
                }
            return None
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def get_comments(self, video_id, max_results=100, include_replies=False, progress_callback=None):
        """
        Get comments from a YouTube video
        Supports up to 100,000 comments with pagination
        
        Args:
            video_id: YouTube video ID
            max_results: Maximum number of comments (max 100000)
            include_replies: Include reply comments
            progress_callback: Function to report progress (current, total)
        """
        comments = []
        next_page_token = None
        page_count = 0
        
        # Limit max_results to 100000
        max_results = min(max_results, 100000)
        
        try:
            url = f"{self.base_url}/commentThreads"
            headers = {
                'Referer': 'http://localhost:5000/'
            }
            
            while len(comments) < max_results:
                page_count += 1
                
                # Calculate optimal batch size (max 100 per request)
                batch_size = min(100, max_results - len(comments))
                
                params = {
                    'part': 'snippet,replies',
                    'videoId': video_id,
                    'maxResults': batch_size,
                    'textFormat': 'plainText',
                    'order': 'relevance',  # relevance, time
                    'key': self.api_key
                }
                
                if next_page_token:
                    params['pageToken'] = next_page_token
                
                # Make API request
                response = requests.get(url, params=params, headers=headers)
                
                # Check for errors
                if response.status_code == 403:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_reason = error_data['error'].get('errors', [{}])[0].get('reason', '')
                        if error_reason == 'commentsDisabled':
                            print("Error: Komentar dinonaktifkan untuk video ini")
                            return comments if comments else []
                        elif error_reason == 'quotaExceeded':
                            print(f"Warning: Quota exceeded. Returning {len(comments)} comments")
                            return comments
                
                response.raise_for_status()
                data = response.json()
                
                # Extract comments from current page
                items = data.get('items', [])
                if not items:
                    print(f"No more comments found. Total: {len(comments)}")
                    break
                
                for item in items:
                    comment = item['snippet']['topLevelComment']['snippet']
                    comment_data = {
                        'author': comment['authorDisplayName'],
                        'text': comment['textDisplay'],
                        'likes': comment['likeCount'],
                        'published_at': comment['publishedAt'],
                        'reply_count': item['snippet']['totalReplyCount']
                    }
                    
                    # Add replies if requested
                    if include_replies and 'replies' in item:
                        replies = []
                        for reply_item in item['replies']['comments']:
                            reply = reply_item['snippet']
                            replies.append({
                                'author': reply['authorDisplayName'],
                                'text': reply['textDisplay'],
                                'likes': reply['likeCount'],
                                'published_at': reply['publishedAt']
                            })
                        comment_data['replies'] = replies
                    
                    comments.append(comment_data)
                    
                    # Report progress
                    if progress_callback:
                        progress_callback(len(comments), max_results)
                    
                    if len(comments) >= max_results:
                        break
                
                # Check for next page
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    print(f"Reached end of available comments. Total: {len(comments)}")
                    break
                
                # Progress info
                print(f"Page {page_count}: Fetched {len(comments)}/{max_results} comments")
            
            print(f"Successfully fetched {len(comments)} comments in {page_count} pages")
            return comments
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                error_msg = "Komentar dinonaktifkan untuk video ini atau API key tidak valid"
                print(f"Error: {error_msg}")
            elif e.response.status_code == 400:
                print("Error: Invalid request. Check video ID")
            else:
                print(f"HTTP Error {e.response.status_code}: {e}")
            
            # Return comments collected so far
            return comments if comments else []
            
        except Exception as e:
            print(f"Error getting comments: {e}")
            return comments if comments else []
