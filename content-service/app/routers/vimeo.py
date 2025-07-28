# app/routers/vimeo.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import os
from typing import Optional
from uuid import UUID
import uuid
from datetime import datetime

# You'll need to install: pip install python-vimeo
try:
    import vimeo
    # Check what's actually available in the vimeo module
    vimeo_attributes = dir(vimeo)
    print(f"🔍 Available vimeo attributes: {vimeo_attributes}")
except ImportError:
    vimeo = None
    vimeo_attributes = []

from app.db.session import get_db, settings
from app.dependencies.roles import require_any_role
from app.crud.lesson import create_lesson as crud_create_lesson, get_lessons_by_module
from app.schemas.lesson import LessonCreate

router = APIRouter(prefix="/vimeo", tags=["Vimeo Integration"])

# Vimeo Configuration - Load from settings (which reads .env file)
VIMEO_CLIENT_ID = settings.VIMEO_CLIENT_ID
VIMEO_CLIENT_SECRET = settings.VIMEO_CLIENT_SECRET
VIMEO_ACCESS_TOKEN = settings.VIMEO_ACCESS_TOKEN

# Initialize Vimeo client
vimeo_client = None
print(f"🔧 Vimeo Config Check:")
print(f"   CLIENT_ID: {VIMEO_CLIENT_ID[:20]}..." if VIMEO_CLIENT_ID else "   CLIENT_ID: Not set")
print(f"   CLIENT_SECRET: {VIMEO_CLIENT_SECRET[:20]}..." if VIMEO_CLIENT_SECRET else "   CLIENT_SECRET: Not set")
print(f"   ACCESS_TOKEN: {VIMEO_ACCESS_TOKEN[:20]}..." if VIMEO_ACCESS_TOKEN else "   ACCESS_TOKEN: Not set")

if vimeo and VIMEO_CLIENT_ID and VIMEO_CLIENT_SECRET and VIMEO_ACCESS_TOKEN:
    try:
        # Try different possible class names
        if hasattr(vimeo, 'VimeoApi'):
            vimeo_client = vimeo.VimeoApi(VIMEO_CLIENT_ID, VIMEO_CLIENT_SECRET, VIMEO_ACCESS_TOKEN)
        elif hasattr(vimeo, 'VimeoClient'):
            vimeo_client = vimeo.VimeoClient(
                token=VIMEO_ACCESS_TOKEN,
                key=VIMEO_CLIENT_ID,
                secret=VIMEO_CLIENT_SECRET
            )
        elif hasattr(vimeo, 'Client'):
            vimeo_client = vimeo.Client(
                token=VIMEO_ACCESS_TOKEN,
                key=VIMEO_CLIENT_ID,
                secret=VIMEO_CLIENT_SECRET
            )
        else:
            print(f"❌ Unknown Vimeo API class. Available: {dir(vimeo)}")
            vimeo_client = None
        
        if vimeo_client:
            print("✅ Vimeo client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize Vimeo client: {e}")
else:
    print("❌ Vimeo not configured - missing credentials or python-vimeo package")

class VimeoUploadRequest(BaseModel):
    size: int
    name: str

class VimeoMetadataUpdate(BaseModel):
    name: str
    description: Optional[str] = None

class LessonCreateWithVimeo(BaseModel):
    moduleid: UUID
    title: str
    title_fr: Optional[str] = None
    content: Optional[str] = None
    orderindex: Optional[int] = None
    video_url: str
    vimeo_id: str
    video_type: str = "vimeo"

@router.get("/upload-status")
async def check_upload_access_status():
    """Check if your Vimeo app has upload access approved"""
    if not vimeo_client:
        raise HTTPException(
            status_code=503,
            detail="Vimeo integration not configured"
        )
    
    try:
        # Try to create a simple upload request to test permissions
        response = vimeo_client.post('/me/videos', data={
            'name': 'Upload Access Test',
            'privacy': {'view': 'unlisted'}
        })
        
        if response.status_code == 201:
            # Success - delete the test video immediately
            upload_data = response.json()
            video_id = upload_data['uri'].split('/')[-1]
            try:
                vimeo_client.delete(f'/videos/{video_id}')
            except:
                pass  # Ignore delete errors
            
            return {
                "upload_access": "approved",
                "status": "✅ Upload access approved!",
                "message": "Your app can now upload videos",
                "ready_to_use": True
            }
        else:
            error_detail = response.text
            if "upload" in error_detail.lower() and ("scope" in error_detail.lower() or "permission" in error_detail.lower()):
                return {
                    "upload_access": "under_review",
                    "status": "⏳ Upload access still under review",
                    "message": "Your upload request is being reviewed by Vimeo",
                    "ready_to_use": False,
                    "estimated_time": "1-3 business days (can take up to 2 weeks)",
                    "next_steps": [
                        "Wait for Vimeo's review process",
                        "Check https://developer.vimeo.com/apps for status updates",
                        "Contact Vimeo support if urgent: https://vimeo.com/help/contact"
                    ],
                    "vimeo_response": error_detail
                }
            else:
                return {
                    "upload_access": "unknown_error",
                    "status": "❌ Unknown error",
                    "message": "Unexpected error checking upload access",
                    "vimeo_response": error_detail
                }
            
    except Exception as e:
        return {
            "upload_access": "error",
            "status": "❌ Error checking status",
            "message": str(e)
        }

@router.get("/api-info")
async def vimeo_api_info():
    """Information about Vimeo API upload capabilities and free tier"""
    return {
        "free_tier_api_upload": {
            "available": True,
            "limitations": {
                "weekly_upload": "500 MB per week",
                "total_storage": "5 GB total",
                "daily_uploads": "10 uploads per day",
                "max_file_size": "No specific limit (beyond storage)",
                "max_duration": "No limit"
            },
            "what_you_get": [
                "Full API access including uploads",
                "No ads on your videos",
                "Unlisted video privacy",
                "Basic analytics",
                "Embed anywhere"
            ]
        },
        "your_current_issue": {
            "problem": "Missing upload scope in access token",
            "not_about": "Free tier limitations",
            "solution": "Generate new token with upload scope checked"
        },
        "upgrade_benefits": {
            "starter_12_month": {
                "price": "$12/month",
                "storage": "100GB", 
                "weekly_upload": "5GB per week"
            },
            "standard_25_month": {
                "price": "$25/month", 
                "storage": "2TB",
                "weekly_upload": "20GB per week"
            }
        },
        "api_requirements": {
            "account": "Free Vimeo account (sufficient)",
            "app": "API application (free to create)",
            "token": "Personal access token with 'upload' scope",
            "request_upload_access": "May need to request upload access for your app"
        }
    }

@router.get("/auth/fix-token")
async def fix_vimeo_token():
    """Instructions to fix the upload scope issue"""
    return {
        "problem": "Your access token doesn't have the 'upload' scope",
        "solution_1_personal_token": {
            "title": "Generate New Personal Access Token (Easiest)",
            "steps": [
                "1. Go to https://developer.vimeo.com/apps",
                "2. Click on your app",
                "3. Go to 'Authentication' tab",
                "4. Scroll down to 'Personal access tokens'",
                "5. Click 'Generate new token'",
                "6. Select these scopes: 'public', 'private', 'upload', 'delete', 'edit'",
                "7. Copy the generated token",
                "8. Update your .env file: VIMEO_ACCESS_TOKEN=your_new_token",
                "9. Restart your application"
            ],
            "important": "Make sure to check the 'upload' scope checkbox!"
        },
        "solution_2_oauth": {
            "title": "Use OAuth Flow (More Complex)",
            "steps": [
                "1. Use /vimeo/auth/generate-url endpoint",
                "2. Follow the OAuth process",
                "3. Exchange code for token with upload scope"
            ]
        },
        "current_token_scopes": "Your current token likely only has 'public' scope",
        "required_scopes": ["public", "private", "upload", "delete", "edit"]
    }

@router.get("/auth/generate-url")
async def generate_vimeo_auth_url():
    """Generate Vimeo OAuth URL to get a user access token with upload permissions"""
    if not VIMEO_CLIENT_ID or not VIMEO_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Vimeo client credentials not configured"
        )
    
    # Vimeo OAuth URL with upload scope
    oauth_url = (
        f"https://vimeo.com/oauth/authorize"
        f"?response_type=code"
        f"&client_id={VIMEO_CLIENT_ID}"
        f"&redirect_uri=https://localhost:8000/vimeo/auth/callback"  # You'll need to set this in Vimeo app settings
        f"&scope=public private upload delete edit"
        f"&state=auth_request"
    )
    
    return {
        "oauth_url": oauth_url,
        "instructions": [
            "1. Visit the oauth_url above",
            "2. Authorize your app",
            "3. You'll be redirected with a 'code' parameter",
            "4. Use that code with /auth/exchange-token endpoint",
            "5. Update your .env file with the new access token"
        ],
        "redirect_uri_note": "Make sure to add the redirect_uri to your Vimeo app settings at https://developer.vimeo.com/apps"
    }

@router.post("/auth/exchange-token")
async def exchange_vimeo_token(code: str):
    """Exchange authorization code for user access token"""
    if not vimeo_client:
        raise HTTPException(
            status_code=503,
            detail="Vimeo client not configured"
        )
    
    try:
        # Exchange code for access token
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': 'https://localhost:8000/vimeo/auth/callback'
        }
        
        # Use basic auth with client credentials
        import base64
        credentials = base64.b64encode(f"{VIMEO_CLIENT_ID}:{VIMEO_CLIENT_SECRET}".encode()).decode()
        
        import requests
        response = requests.post(
            'https://api.vimeo.com/oauth/access_token',
            data=token_data,
            headers={'Authorization': f'Basic {credentials}'}
        )
        
        if response.status_code == 200:
            token_info = response.json()
            return {
                "access_token": token_info.get('access_token'),
                "scope": token_info.get('scope'),
                "token_type": token_info.get('token_type'),
                "user": token_info.get('user'),
                "instructions": [
                    "Update your .env file:",
                    f"VIMEO_ACCESS_TOKEN={token_info.get('access_token')}",
                    "Then restart your application"
                ]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Token exchange failed: {response.text}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exchanging token: {str(e)}"
        )

@router.get("/test-token")
async def test_vimeo_token():
    """Test if the current Vimeo token has proper permissions"""
    if not vimeo_client:
        raise HTTPException(
            status_code=503,
            detail="Vimeo integration not configured"
        )
    
    try:
        # Test basic API access
        me_response = vimeo_client.get('/me')
        
        if me_response.status_code == 200:
            user_data = me_response.json()
            
            # Test quota (upload permissions)
            quota_response = vimeo_client.get('/me/videos')
            quota_works = quota_response.status_code == 200
            
            return {
                "token_valid": True,
                "user_id": user_data.get('uri'),
                "user_name": user_data.get('name'),
                "account_type": user_data.get('account'),
                "upload_quota": user_data.get('upload_quota'),
                "can_access_videos": quota_works,
                "token_has_user_context": bool(user_data.get('uri')),
                "recommendation": "Token looks good!" if quota_works else "Token may lack upload permissions"
            }
        else:
            return {
                "token_valid": False,
                "error": me_response.text,
                "recommendation": "Get a new user access token using /auth/generate-url"
            }
            
    except Exception as e:
        return {
            "token_valid": False,
            "error": str(e),
            "recommendation": "Get a new user access token using /auth/generate-url"
        }

@router.get("/debug/config")
async def debug_vimeo_config():
    """Debug endpoint to check Vimeo configuration"""
    error_msg = None
    
    # Try to create a fresh client to see the exact error
    if vimeo and VIMEO_CLIENT_ID and VIMEO_CLIENT_SECRET and VIMEO_ACCESS_TOKEN:
        try:
            # Try different possible class names
            if hasattr(vimeo, 'VimeoApi'):
                test_client = vimeo.VimeoApi(VIMEO_CLIENT_ID, VIMEO_CLIENT_SECRET, VIMEO_ACCESS_TOKEN)
            elif hasattr(vimeo, 'VimeoClient'):
                test_client = vimeo.VimeoClient(
                    token=VIMEO_ACCESS_TOKEN,
                    key=VIMEO_CLIENT_ID,
                    secret=VIMEO_CLIENT_SECRET
                )
            elif hasattr(vimeo, 'Client'):
                test_client = vimeo.Client(
                    token=VIMEO_ACCESS_TOKEN,
                    key=VIMEO_CLIENT_ID,
                    secret=VIMEO_CLIENT_SECRET
                )
            else:
                test_client = None
                error_msg = f"Unknown Vimeo API class. Available: {vimeo_attributes}"
            
            if test_client:
                error_msg = "No error - client created successfully"
        except Exception as e:
            error_msg = str(e)
    
    return {
        "vimeo_package_available": vimeo is not None,
        "client_id_set": bool(VIMEO_CLIENT_ID),
        "client_secret_set": bool(VIMEO_CLIENT_SECRET), 
        "access_token_set": bool(VIMEO_ACCESS_TOKEN),
        "vimeo_client_initialized": vimeo_client is not None,
        "client_id_preview": VIMEO_CLIENT_ID[:20] + "..." if VIMEO_CLIENT_ID else "None",
        "settings_loaded": bool(settings.VIMEO_CLIENT_ID),
        "initialization_error": error_msg,
        "credentials_preview": {
            "client_id_length": len(VIMEO_CLIENT_ID) if VIMEO_CLIENT_ID else 0,
            "client_secret_length": len(VIMEO_CLIENT_SECRET) if VIMEO_CLIENT_SECRET else 0,
            "access_token_length": len(VIMEO_ACCESS_TOKEN) if VIMEO_ACCESS_TOKEN else 0
        }
    }

@router.post("/create-simple-upload")
async def create_simple_vimeo_upload(
    name: str = "Test Video",
    user = Depends(require_any_role("admin", "teacher"))
):
    """Create a simple Vimeo upload without size restrictions - good for testing"""
    if not vimeo_client:
        raise HTTPException(
            status_code=503,
            detail="Vimeo integration not configured."
        )
    
    try:
        # Simple upload request without size specification
        response = vimeo_client.post('/me/videos', data={
            'name': name,
            'privacy': {
                'view': 'unlisted'
            }
        })
        
        if response.status_code == 201:
            upload_data = response.json()
            video_id = upload_data['uri'].split('/')[-1]
            
            return {
                "upload_url": upload_data.get('upload', {}).get('upload_link'),
                "video_id": video_id,
                "vimeo_player_url": f"https://player.vimeo.com/video/{video_id}",
                "video_uri": upload_data['uri'],
                "status": "created",
                "upload_approach": upload_data.get('upload', {}).get('approach'),
                "message": "Simple upload created successfully"
            }
        else:
            error_detail = response.text
            return {
                "error": f"Upload failed: {error_detail}",
                "status_code": response.status_code,
                "response": response.text
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating simple upload: {str(e)}"
        )

@router.post("/create-upload")
async def create_vimeo_upload(
    request: VimeoUploadRequest,
    user = Depends(require_any_role("admin", "teacher"))
):
    """Create a Vimeo upload ticket for resumable uploads"""
    if not vimeo_client:
        raise HTTPException(
            status_code=503,
            detail="Vimeo integration not configured. Please set VIMEO_CLIENT_ID, VIMEO_CLIENT_SECRET, and VIMEO_ACCESS_TOKEN environment variables."
        )
    
    try:
        # For free accounts, try a simpler upload approach first
        upload_data = {
            'name': request.name,
            'privacy': {
                'view': 'unlisted'  # Good balance: not searchable but shareable with link
            }
        }
        
        # Only add upload size if it's reasonable for free accounts (< 500MB)
        if request.size < 500 * 1024 * 1024:  # 500MB limit for free accounts
            upload_data['upload'] = {
                'approach': 'tus',
                'size': request.size
            }
        else:
            # For larger files, let Vimeo handle the upload approach
            upload_data['upload'] = {
                'approach': 'tus'
            }
        
        # Create upload ticket
        response = vimeo_client.post('/me/videos', data=upload_data)
        
        if response.status_code == 201:
            upload_data = response.json()
            return {
                "upload_url": upload_data['upload']['upload_link'],
                "upload_ticket": upload_data['upload']['upload_link'],
                "video_id": upload_data['uri'].split('/')[-1],
                "vimeo_player_url": f"https://player.vimeo.com/video/{upload_data['uri'].split('/')[-1]}",
                "status": "created"
            }
        else:
            # Handle specific Vimeo API errors
            error_detail = response.text
            if "8002" in error_detail or "missing a user ID" in error_detail:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Invalid access token - user authentication required",
                        "solution": "Your access token doesn't have user context for uploads",
                        "steps": [
                            "1. Visit /vimeo/auth/generate-url to get OAuth URL",
                            "2. Authorize your app and get the authorization code",
                            "3. Use /vimeo/auth/exchange-token with the code",
                            "4. Update your .env file with the new user access token",
                            "5. Restart the application"
                        ],
                        "vimeo_error": error_detail
                    }
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to create Vimeo upload ticket: {error_detail}"
                )
            
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating upload ticket: {str(e)}"
        )

@router.patch("/update-metadata/{video_id}")
async def update_vimeo_metadata(
    video_id: str,
    metadata: VimeoMetadataUpdate,
    user = Depends(require_any_role("admin", "teacher"))
):
    """Update video metadata on Vimeo"""
    if not vimeo_client:
        raise HTTPException(
            status_code=503,
            detail="Vimeo integration not configured."
        )
    
    try:
        response = vimeo_client.patch(f'/videos/{video_id}', data={
            'name': metadata.name,
            'description': metadata.description
        })
        
        if response.status_code == 200:
            return {"status": "updated", "video_id": video_id}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update video metadata: {response.text}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating metadata: {str(e)}"
        )

@router.post("/create-lesson")
async def create_lesson_with_vimeo(
    lesson: LessonCreateWithVimeo,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin", "teacher"))
):
    """Create a new lesson in the database with Vimeo video"""
    try:
        # Convert to standard LessonCreate schema with video information
        lesson_create = LessonCreate(
            moduleid=lesson.moduleid,
            title=lesson.title,
            title_fr=lesson.title_fr,
            content=lesson.content,
            orderindex=lesson.orderindex,
            completed=False,
            video=lesson.video_url,  # Store the full video URL
            vimeo_id=lesson.vimeo_id,  # Store the Vimeo ID
            video_type=lesson.video_type  # Store the video type
        )
        
        # Create the lesson with all video information
        created_lesson = await crud_create_lesson(db, lesson_create)
        
        return {
            "status": "created",
            "lesson_id": str(created_lesson.id),
            "vimeo_id": lesson.vimeo_id,
            "video_url": lesson.video_url,
            "video_type": lesson.video_type,
            "message": "Lesson created successfully with Vimeo video"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating lesson: {str(e)}"
        )

@router.put("/update-lesson-video/{lesson_id}")
async def update_lesson_video(
    lesson_id: UUID,
    video_url: str,
    vimeo_id: str,
    video_type: str = "vimeo",
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin", "teacher"))
):
    """Update an existing lesson with video information"""
    try:
        from app.crud.lesson import get_lesson, update_lesson
        from app.schemas.lesson import LessonUpdate
        
        # Check if lesson exists
        existing_lesson = await get_lesson(db, lesson_id)
        if not existing_lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Create update schema with current values plus video info
        lesson_update = LessonUpdate(
            moduleid=existing_lesson.moduleid,
            title=existing_lesson.title,
            title_fr=existing_lesson.title_fr,
            content=existing_lesson.content,
            orderindex=existing_lesson.orderindex,
            completed=existing_lesson.completed,
            video=video_url,  # Update video URL
            vimeo_id=vimeo_id,  # Update Vimeo ID
            video_type=video_type  # Update video type
        )
        
        # Update the lesson
        updated_lesson = await update_lesson(db, lesson_id, lesson_update)
        
        return {
            "status": "updated",
            "lesson_id": str(lesson_id),
            "video_url": video_url,
            "vimeo_id": vimeo_id,
            "video_type": video_type,
            "message": "Lesson video updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating lesson video: {str(e)}"
        )

@router.post("/complete-upload")
async def complete_vimeo_upload_workflow(
    lesson_id: UUID,
    vimeo_video_id: str,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_any_role("admin", "teacher"))
):
    """Complete the Vimeo upload workflow by updating lesson with video info"""
    try:
        # Generate the embed URL
        video_url = f"https://player.vimeo.com/video/{vimeo_video_id}"
        
        # Update the lesson
        result = await update_lesson_video(
            lesson_id=lesson_id,
            video_url=video_url,
            vimeo_id=vimeo_video_id,
            video_type="vimeo",
            db=db,
            user=user
        )
        
        # Also update Vimeo privacy to unlisted for better security
        if vimeo_client:
            try:
                vimeo_client.patch(f'/videos/{vimeo_video_id}', data={
                    'privacy': {'view': 'unlisted'}
                })
            except Exception as e:
                print(f"Warning: Could not update Vimeo privacy: {e}")
        
        return {
            **result,
            "embed_url": video_url,
            "workflow": "completed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error completing upload workflow: {str(e)}"
        )

@router.get("/video-info/{video_id}")
async def get_vimeo_video_info(
    video_id: str,
    user = Depends(require_any_role("admin", "teacher", "student"))
):
    """Get video information from Vimeo"""
    if not vimeo_client:
        raise HTTPException(
            status_code=503,
            detail="Vimeo integration not configured."
        )
    
    try:
        response = vimeo_client.get(f'/videos/{video_id}')
        
        if response.status_code == 200:
            video_data = response.json()
            return {
                "video_id": video_id,
                "name": video_data.get('name'),
                "description": video_data.get('description'),
                "duration": video_data.get('duration'),
                "player_embed_url": video_data.get('player_embed_url'),
                "thumbnail": video_data.get('pictures', {}).get('sizes', [{}])[-1].get('link'),
                "status": video_data.get('status'),
                "privacy": video_data.get('privacy', {}).get('view')
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get video info: {response.text}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting video info: {str(e)}"
        )

@router.delete("/video/{video_id}")
async def delete_vimeo_video(
    video_id: str,
    user = Depends(require_any_role("admin", "teacher"))
):
    """Delete a video from Vimeo"""
    if not vimeo_client:
        raise HTTPException(
            status_code=503,
            detail="Vimeo integration not configured."
        )
    
    try:
        response = vimeo_client.delete(f'/videos/{video_id}')
        
        if response.status_code == 204:
            return {"status": "deleted", "video_id": video_id}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to delete video: {response.text}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting video: {str(e)}"
        )

# Utility function
def generate_vimeo_embed_url(video_id: str) -> str:
    """Generate Vimeo embed URL from video ID"""
    return f"https://player.vimeo.com/video/{video_id}"

def extract_vimeo_id_from_url(vimeo_url: str) -> Optional[str]:
    """Extract Vimeo video ID from various Vimeo URL formats"""
    import re
    
    # Common Vimeo URL patterns
    patterns = [
        r'vimeo\.com/(\d+)',
        r'player\.vimeo\.com/video/(\d+)',
        r'vimeo\.com/video/(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, vimeo_url)
        if match:
            return match.group(1)
    
    return None
