import json
import os
from datetime import datetime

class DataStorage:
    def __init__(self, storage_dir='data'):
        self.storage_dir = storage_dir
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
    
    def save_comments(self, video_id, video_info, comments):
        """
        Save scraped comments to a JSON file
        """
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
        Get list of all saved comment files
        """
        files = []
        
        # Ensure storage directory exists
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
            
            # Sort by scraped date (newest first)
            files.sort(key=lambda x: x['scraped_at'], reverse=True)
        except Exception as e:
            print(f"Error listing files: {e}")
        
        return files
    
    def load_comments(self, filename):
        """
        Load comments from a saved file
        """
        filepath = os.path.join(self.storage_dir, filename)
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def delete_file(self, filename):
        """
        Delete a saved comment file
        """
        filepath = os.path.join(self.storage_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
