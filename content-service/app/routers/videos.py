# app/routers/videos.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from app.db.session import get_db
from app.dependencies.roles import require_any_role
from app.crud.lesson import create_lesson as crud_create_lesson
from app.schemas.lesson import LessonCreate
from app.services.video_service import video_service, VideoUploadRequest, VideoMetadata, VideoProvider

router = APIRouter(prefix="/videos", tags=["Video Management"])

class LessonCreateWithVideo(BaseModel):
    moduleid: UUID
    title: str
    title_fr: Optional[str] = None
    content: Optional[str] = None
    orderindex: Optional[int] = None
    video_url: str
    video_id: str
    video_provider: VideoProvider = "apivideo"

@router.get("/providers/status")
async def get_providers_status(user=Depends(require_any_role("admin", "teacher"))):
    """Get status of all video providers (API.video, Vimeo)"""
    return await video_service.get_provider_status()

@router.post("/create", response_model=VideoMetadata)
async def create_video(
    request: VideoUploadRequest, 
    user=Depends(require_any_role("admin", "teacher"))
):
    """
    Create a video on the specified provider (API.video or Vimeo).
    API.video is recommended as it's free for reasonable usage.
    """
    return await video_service.create_video(request)

@router.get("/info/{provider}/{video_id}", response_model=VideoMetadata)
async def get_video_info(
    provider: VideoProvider,
    video_id: str,
    user=Depends(require_any_role("admin", "teacher", "student"))
):
    """Get video information from the specified provider"""
    return await video_service.get_video_info(video_id, provider)

@router.delete("/{provider}/{video_id}")
async def delete_video(
    provider: VideoProvider,
    video_id: str,
    user=Depends(require_any_role("admin", "teacher"))
):
    """Delete a video from the specified provider"""
    return await video_service.delete_video(video_id, provider)

@router.post("/lessons", status_code=status.HTTP_201_CREATED)
async def create_lesson_with_video(
    lesson: LessonCreateWithVideo,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_any_role("admin", "teacher"))
):
    """Create a lesson with video from any provider"""
    try:
        # Verify video exists and get its info
        video_info = await video_service.get_video_info(lesson.video_id, lesson.video_provider)
        
        # Create lesson with video information
        lesson_create = LessonCreate(
            moduleid=lesson.moduleid,
            title=lesson.title,
            title_fr=lesson.title_fr,
            content=lesson.content or "",
            orderindex=lesson.orderindex or 0,
            completed=False,
            video=lesson.video_url,
            vimeo_id=lesson.video_id,  # Using vimeo_id field for all video IDs (legacy naming)
            video_type=lesson.video_provider
        )
        
        created_lesson = await crud_create_lesson(db, lesson_create)
        
        return {
            "status": "created",
            "lesson_id": str(created_lesson.id),
            "lesson_title": created_lesson.title,
            "video_id": lesson.video_id,
            "video_url": lesson.video_url,
            "video_provider": lesson.video_provider,
            "video_info": video_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create lesson: {str(e)}")

# Legacy compatibility endpoints
@router.post("/apivideo/create-video")
async def create_apivideo_legacy(
    name: str,
    description: str = "",
    privacy: str = "unlisted",
    user=Depends(require_any_role("admin", "teacher"))
):
    """Legacy endpoint for API.video - use /videos/create instead"""
    request = VideoUploadRequest(name=name, description=description, privacy=privacy, provider="apivideo")
    return await video_service.create_video(request)

@router.post("/vimeo/create-video") 
async def create_vimeo_legacy(
    name: str,
    description: str = "",
    privacy: str = "unlisted",
    user=Depends(require_any_role("admin", "teacher"))
):
    """Legacy endpoint for Vimeo - use /videos/create instead"""
    request = VideoUploadRequest(name=name, description=description, privacy=privacy, provider="vimeo")
    return await video_service.create_video(request)

@router.get("/upload-guide")
async def get_upload_guide(user=Depends(require_any_role("admin", "teacher"))):
    """Get upload guide for both video providers"""
    provider_status = await video_service.get_provider_status()
    
    guide = {
        "recommended_provider": provider_status.get("recommended", "apivideo"),
        "providers": {
            "apivideo": {
                "name": "API.video",
                "advantages": [
                    "Free tier: 10GB storage, 100GB bandwidth/month",
                    "No upload approval required",
                    "Instant setup with API key",
                    "Good performance and reliability",
                    "Modern API design"
                ],
                "setup_steps": [
                    "1. Go to https://api.video and create free account",
                    "2. Get your API key from dashboard",
                    "3. Set APIVIDEO_KEY environment variable",
                    "4. Ready to upload!"
                ],
                "status": provider_status["apivideo"]
            },
            "vimeo": {
                "name": "Vimeo",
                "advantages": [
                    "Professional video hosting",
                    "Good video quality",
                    "Established platform"
                ],
                "disadvantages": [
                    "Upload API requires manual approval (can take days/weeks)",
                    "More complex OAuth setup",
                    "Stricter rate limits"
                ],
                "setup_steps": [
                    "1. Create Vimeo developer app",
                    "2. Request upload permission (wait for approval)",
                    "3. Set VIMEO_CLIENT_ID, VIMEO_CLIENT_SECRET, VIMEO_ACCESS_TOKEN",
                    "4. Ready to upload (after approval)"
                ],
                "status": provider_status["vimeo"]
            }
        },
        "migration_note": "You can use both providers simultaneously. Existing lessons will continue working.",
        "frontend_integration": {
            "create_video_endpoint": "/videos/create",
            "check_status_endpoint": "/videos/providers/status",
            "upload_flow": [
                "1. Check provider status",
                "2. Create video with preferred provider", 
                "3. Get upload URL from response",
                "4. Upload video file to the URL",
                "5. Create lesson with video details"
            ]
        }
    }
    
    return guide
