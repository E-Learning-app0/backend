# app/services/vimeo_service.py
import os
import re
from typing import Optional, Dict, Any
try:
    import vimeo
except ImportError:
    vimeo = None

class VimeoService:
    def __init__(self):
        self.client_id = os.getenv("VIMEO_CLIENT_ID")
        self.client_secret = os.getenv("VIMEO_CLIENT_SECRET")
        self.access_token = os.getenv("VIMEO_ACCESS_TOKEN")
        
        self.client = None
        if vimeo and self.client_id and self.client_secret and self.access_token:
            try:
                self.client = vimeo.VimeoApi(self.client_id, self.client_secret, self.access_token)
            except Exception as e:
                print(f"Warning: Failed to initialize Vimeo client: {e}")
    
    def is_configured(self) -> bool:
        """Check if Vimeo is properly configured"""
        return self.client is not None
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract Vimeo video ID from various URL formats"""
        patterns = [
            r'vimeo\.com/(\d+)',
            r'player\.vimeo\.com/video/(\d+)',
            r'vimeo\.com/video/(\d+)',
            r'vimeo\.com/channels/[\w-]+/(\d+)',
            r'vimeo\.com/groups/[\w-]+/videos/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If it's already just a video ID
        if url.isdigit():
            return url
            
        return None
    
    def generate_embed_url(self, video_id: str, **params) -> str:
        """Generate Vimeo embed URL with optional parameters"""
        base_url = f"https://player.vimeo.com/video/{video_id}"
        
        # Common embed parameters
        default_params = {
            'badge': '0',
            'autopause': '0',
            'player_id': '0',
            'app_id': '58479'
        }
        
        # Merge with provided parameters
        all_params = {**default_params, **params}
        
        if all_params:
            param_string = '&'.join([f"{k}={v}" for k, v in all_params.items()])
            return f"{base_url}?{param_string}"
        
        return base_url
    
    def generate_thumbnail_url(self, video_id: str, size: str = "640x360") -> str:
        """Generate Vimeo thumbnail URL"""
        return f"https://vumbnail.com/{video_id}_{size}.jpg"
    
    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video information from Vimeo API"""
        if not self.client:
            return None
        
        try:
            response = self.client.get(f'/videos/{video_id}')
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting video info: {e}")
        
        return None
    
    async def update_video_privacy(self, video_id: str, privacy: str = "unlisted") -> bool:
        """Update video privacy settings"""
        if not self.client:
            return False
        
        try:
            response = self.client.patch(f'/videos/{video_id}', data={
                'privacy': {'view': privacy}
            })
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating video privacy: {e}")
            return False
    
    async def delete_video(self, video_id: str) -> bool:
        """Delete video from Vimeo"""
        if not self.client:
            return False
        
        try:
            response = self.client.delete(f'/videos/{video_id}')
            return response.status_code == 204
        except Exception as e:
            print(f"Error deleting video: {e}")
            return False

# Global instance
vimeo_service = VimeoService()
