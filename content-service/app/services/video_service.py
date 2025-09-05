# app/services/video_service.py
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal
import os
from datetime import datetime
from uuid import UUID

# API.video imports
try:
    from apivideo import ApiClient, VideosApi, Configuration
    apivideo_available = True
except ImportError:
    apivideo_available = False
    print("⚠️ API.video SDK not available. Install with: pip install apivideo-python")

# Vimeo imports
try:
    import vimeo
    vimeo_available = True
except ImportError:
    vimeo_available = False
    print("⚠️ Vimeo SDK not available. Install with: pip install python-vimeo")

VideoProvider = Literal["apivideo", "vimeo"]

class VideoUploadRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    privacy: str = "unlisted"  # "public", "unlisted", "private"
    provider: VideoProvider = "apivideo"  # Default to API.video

class VideoMetadata(BaseModel):
    video_id: str
    title: str
    description: Optional[str] = ""
    provider: VideoProvider
    upload_url: Optional[str] = None
    player_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    status: str = "pending"  # pending, processing, ready, error

class VideoService:
    def __init__(self):
        # Initialize API.video
        self.apivideo_client = None
        self.apivideo_api = None
        if apivideo_available:
            api_key = os.getenv("APIVIDEO_KEY")
            if api_key:
                try:
                    config = Configuration(api_key={"apiKeyAuth": api_key})
                    self.apivideo_client = ApiClient(configuration=config)
                    self.apivideo_api = VideosApi(self.apivideo_client)
                    print("✅ API.video client initialized")
                except Exception as e:
                    print(f"❌ Failed to initialize API.video client: {e}")
        
        # Initialize Vimeo
        self.vimeo_client = None
        if vimeo_available:
            client_id = os.getenv("VIMEO_CLIENT_ID")
            client_secret = os.getenv("VIMEO_CLIENT_SECRET") 
            access_token = os.getenv("VIMEO_ACCESS_TOKEN")
            
            if client_id and client_secret and access_token:
                try:
                    # Try different possible class names for vimeo client
                    if hasattr(vimeo, 'VimeoApi'):
                        self.vimeo_client = vimeo.VimeoApi(client_id, client_secret, access_token)
                    elif hasattr(vimeo, 'VimeoClient'):
                        self.vimeo_client = vimeo.VimeoClient(
                            token=access_token, key=client_id, secret=client_secret
                        )
                    elif hasattr(vimeo, 'Client'):
                        self.vimeo_client = vimeo.Client(
                            token=access_token, key=client_id, secret=client_secret
                        )
                    print("✅ Vimeo client initialized")
                except Exception as e:
                    print(f"❌ Failed to initialize Vimeo client: {e}")
    
    async def create_video(self, request: VideoUploadRequest) -> VideoMetadata:
        """Create a video on the specified provider"""
        if request.provider == "apivideo":
            return await self._create_apivideo(request)
        elif request.provider == "vimeo":
            return await self._create_vimeo_video(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")
    
    async def _create_apivideo(self, request: VideoUploadRequest) -> VideoMetadata:
        """Create video using API.video"""
        if not self.apivideo_api:
            raise HTTPException(status_code=503, detail="API.video not configured")
        
        try:
            video_payload = {
                "title": request.name,
                "description": request.description or "",
                "public": request.privacy == "public"
            }
            
            response = self.apivideo_api.create(video_payload)
            
            return VideoMetadata(
                video_id=response.video_id,
                title=request.name,
                description=request.description or "",
                provider="apivideo",
                upload_url=response.assets.iframe if hasattr(response.assets, 'iframe') else None,
                player_url=response.assets.iframe if hasattr(response.assets, 'iframe') else f"https://embed.api.video/vod/{response.video_id}",
                thumbnail_url=response.assets.thumbnail if hasattr(response.assets, 'thumbnail') else None,
                status="pending"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"API.video error: {str(e)}")
    
    async def _create_vimeo_video(self, request: VideoUploadRequest) -> VideoMetadata:
        """Create video using Vimeo"""
        if not self.vimeo_client:
            raise HTTPException(status_code=503, detail="Vimeo not configured")
        
        try:
            privacy_mapping = {
                "public": "anybody",
                "unlisted": "unlisted", 
                "private": "nobody"
            }
            
            video_data = {
                'name': request.name,
                'description': request.description or "",
                'privacy': {
                    'view': privacy_mapping.get(request.privacy, "unlisted")
                }
            }
            
            response = self.vimeo_client.post('/me/videos', data=video_data)
            
            if response.status_code == 201:
                video_info = response.json()
                video_id = video_info['uri'].split('/')[-1]
                
                return VideoMetadata(
                    video_id=video_id,
                    title=request.name,
                    description=request.description or "",
                    provider="vimeo",
                    upload_url=video_info.get('upload', {}).get('upload_link'),
                    player_url=video_info.get('player_embed_url') or f"https://player.vimeo.com/video/{video_id}",
                    thumbnail_url=None,  # Vimeo generates thumbnails after upload
                    status="pending"
                )
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Vimeo error: {str(e)}")
    
    async def get_video_info(self, video_id: str, provider: VideoProvider) -> VideoMetadata:
        """Get video information from the specified provider"""
        if provider == "apivideo":
            return await self._get_apivideo_info(video_id)
        elif provider == "vimeo":
            return await self._get_vimeo_info(video_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    async def _get_apivideo_info(self, video_id: str) -> VideoMetadata:
        """Get video info from API.video"""
        if not self.apivideo_api:
            raise HTTPException(status_code=503, detail="API.video not configured")
        
        try:
            video = self.apivideo_api.get(video_id)
            return VideoMetadata(
                video_id=video.video_id,
                title=video.title or "",
                description=video.description or "",
                provider="apivideo",
                player_url=video.assets.iframe if hasattr(video.assets, 'iframe') else f"https://embed.api.video/vod/{video_id}",
                thumbnail_url=video.assets.thumbnail if hasattr(video.assets, 'thumbnail') else None,
                duration=getattr(video.assets, 'duration', None),
                status="ready" if hasattr(video.assets, 'iframe') else "processing"
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")
    
    async def _get_vimeo_info(self, video_id: str) -> VideoMetadata:
        """Get video info from Vimeo"""
        if not self.vimeo_client:
            raise HTTPException(status_code=503, detail="Vimeo not configured")
        
        try:
            response = self.vimeo_client.get(f'/videos/{video_id}')
            if response.status_code == 200:
                video_info = response.json()
                return VideoMetadata(
                    video_id=video_id,
                    title=video_info.get('name', ''),
                    description=video_info.get('description', ''),
                    provider="vimeo",
                    player_url=video_info.get('player_embed_url') or f"https://player.vimeo.com/video/{video_id}",
                    thumbnail_url=video_info.get('pictures', {}).get('base_link'),
                    duration=video_info.get('duration'),
                    status=video_info.get('status', 'unknown')
                )
            else:
                raise HTTPException(status_code=404, detail="Video not found")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")
    
    async def delete_video(self, video_id: str, provider: VideoProvider) -> Dict[str, Any]:
        """Delete video from the specified provider"""
        if provider == "apivideo":
            return await self._delete_apivideo(video_id)
        elif provider == "vimeo":
            return await self._delete_vimeo_video(video_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    async def _delete_apivideo(self, video_id: str) -> Dict[str, Any]:
        """Delete video from API.video"""
        if not self.apivideo_api:
            raise HTTPException(status_code=503, detail="API.video not configured")
        
        try:
            self.apivideo_api.delete(video_id)
            return {"status": "deleted", "video_id": video_id, "provider": "apivideo"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")
    
    async def _delete_vimeo_video(self, video_id: str) -> Dict[str, Any]:
        """Delete video from Vimeo"""
        if not self.vimeo_client:
            raise HTTPException(status_code=503, detail="Vimeo not configured")
        
        try:
            response = self.vimeo_client.delete(f'/videos/{video_id}')
            if response.status_code == 204:
                return {"status": "deleted", "video_id": video_id, "provider": "vimeo"}
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all video providers"""
        status = {
            "apivideo": {
                "available": self.apivideo_api is not None,
                "configured": bool(os.getenv("APIVIDEO_KEY")),
                "sdk_installed": apivideo_available
            },
            "vimeo": {
                "available": self.vimeo_client is not None,
                "configured": all([
                    os.getenv("VIMEO_CLIENT_ID"),
                    os.getenv("VIMEO_CLIENT_SECRET"),
                    os.getenv("VIMEO_ACCESS_TOKEN")
                ]),
                "sdk_installed": vimeo_available
            }
        }
        
        # Determine recommended provider
        if status["apivideo"]["available"]:
            status["recommended"] = "apivideo"
        elif status["vimeo"]["available"]:
            status["recommended"] = "vimeo"
        else:
            status["recommended"] = None
            
        return status

# Global video service instance
video_service = VideoService()
