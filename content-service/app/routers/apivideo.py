# app/routers/apivideo.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.session import get_db
from app.dependencies.roles import require_any_role
from app.crud.lesson import create_lesson as crud_create_lesson
from app.schemas.lesson import LessonCreate
import os
import requests

# Install SDK: pip install apivideo-python
from apivideo import ApiClient, VideosApi, Configuration

API_VIDEO_KEY = os.getenv("APIVIDEO_KEY")
if not API_VIDEO_KEY:
    raise RuntimeError("Missing API_VIDEO_KEY in environment variables")

config = Configuration(api_key={"apiKeyAuth": API_VIDEO_KEY})
client = ApiClient(configuration=config)
videos_api = VideosApi(client)

router = APIRouter(prefix="/apivideo", tags=["Api.video Integration"])

class ApiVideoUploadRequest(BaseModel):
    name: str
    description: str = ""
    privacy: str = "unlisted"

class LessonCreateWithApiVideo(BaseModel):
    moduleid: UUID
    title: str
    content: str = ""
    orderindex: int = 0
    video_url: str
    video_id: str
    video_type: str = "apivideo"

@router.post("/create-video")
async def create_video(request: ApiVideoUploadRequest, user=Depends(require_any_role("admin", "teacher"))):
    """Create a new video on api.video"""
    try:
        response = videos_api.create_video(body={
            "title": request.name,
            "description": request.description,
            "privacy": {"view": request.privacy}
        })
        return {
            "video_id": response.video_id,
            "upload_url": response.assets.upload_url,
            "player_url": response.assets.player_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-lesson")
async def create_lesson_with_apivideo(lesson: LessonCreateWithApiVideo, db: AsyncSession = Depends(get_db), user=Depends(require_any_role("admin", "teacher"))):
    """Create a lesson with Api.video link"""
    try:
        lesson_create = LessonCreate(
            moduleid=lesson.moduleid,
            title=lesson.title,
            content=lesson.content,
            orderindex=lesson.orderindex,
            completed=False,
            video=lesson.video_url,
            vimeo_id=lesson.video_id,
            video_type=lesson.video_type
        )
        created_lesson = await crud_create_lesson(db, lesson_create)
        return {
            "status": "created",
            "lesson_id": str(created_lesson.id),
            "video_id": lesson.video_id,
            "video_url": lesson.video_url,
            "video_type": lesson.video_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video-info/{video_id}")
async def get_video_info(video_id: str, user=Depends(require_any_role("admin", "teacher", "student"))):
    """Get video information from api.video"""
    try:
        video = videos_api.get_video(video_id)
        return {
            "video_id": video.video_id,
            "title": video.title,
            "description": video.description,
            "player_url": video.assets.player_url,
            "privacy": video.privacy.view
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/video/{video_id}")
async def delete_video(video_id: str, user=Depends(require_any_role("admin", "teacher"))):
    """Delete a video from api.video"""
    try:
        videos_api.delete_video(video_id)
        return {"status": "deleted", "video_id": video_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.get("/upload-status")
async def check_apivideo_upload_status(user = Depends(require_any_role("admin", "teacher"))):
    """Check if your api.video API key can upload videos"""
    if not API_VIDEO_KEY or not videos_api:
        raise HTTPException(
            status_code=503,
            detail="api.video integration not configured or API key missing"
        )

    try:
        # Create a test video (this will consume a small portion of free quota)
        video_data = videos_api.create_video(name="Upload Access Test", privacy="unlisted")
        video_id = video_data.video_id

        # Delete the test video immediately
        try:
            videos_api.delete_video(video_id)
        except Exception:
            pass  # Ignore delete errors

        return {
            "upload_access": "approved",
            "status": "✅ Upload access approved!",
            "message": "Your API key can now upload videos",
            "ready_to_use": True
        }

    except Exception as e:
        # Common errors: invalid key, quota exceeded, permission issues
        return {
            "upload_access": "error",
            "status": "❌ Error checking upload access",
            "message": str(e)
        }
