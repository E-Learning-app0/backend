
# app/api/v1/endpoints/lessonfiles.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import uuid
import os
from supabase import create_client, Client
from datetime import datetime

from app.db.session import get_db
from app.schemas.lessonfile import LessonFileRead, LessonFileCreate, LessonFileUpdate
from app.crud.lessonfile import (
    get_lessonfile, get_lessonfiles_by_lesson,
    create_lessonfile, update_lessonfile, delete_lessonfile
)
from dotenv import load_dotenv
load_dotenv()
import json
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
AGENT_SERVICE_URL = "http://localhost:8004" 
router = APIRouter(prefix="/lessonfiles", tags=["LessonFiles"])



# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Supabase storage bucket name for PDFs
PDF_BUCKET = "Lessons"


async def upload_to_supabase(file: UploadFile) -> str:
    try:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'pdf'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Read file bytes
        file_content = await file.read()
        file.file.seek(0)

        # Upload file to Supabase
        try:
            upload_response = supabase.storage.from_(PDF_BUCKET).upload(
                path=unique_filename,
                file=file_content,
                file_options={
                    "content-type": file.content_type or "application/pdf",
                    "upsert": False
                }
            )
            
            # Check if upload was successful
            if not upload_response:
                raise HTTPException(status_code=500, detail="File upload failed: Empty response from Supabase")
                
        except Exception as upload_error:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(upload_error)}")

        # Get public URL - handle different response formats
        try:
            public_url_response = supabase.storage.from_(PDF_BUCKET).get_public_url(unique_filename)
            
            # Handle different possible response formats
            if isinstance(public_url_response, str):
                return public_url_response
            elif hasattr(public_url_response, 'public_url'):
                return public_url_response.public_url
            elif isinstance(public_url_response, dict) and 'public_url' in public_url_response:
                return public_url_response['public_url']
            else:
                raise ValueError("Invalid public URL response format")
                
        except Exception as url_error:
            # Clean up the uploaded file if URL generation fails
            try:
                supabase.storage.from_(PDF_BUCKET).remove([unique_filename])
            except Exception as cleanup_error:
                logging.error(f"Failed to cleanup uploaded file: {cleanup_error}")
                
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate public URL: {str(url_error)}"
            )

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}"
        )

async def delete_from_supabase(file_url: str) -> bool:
    try:
        filename = file_url.split('/')[-1].split('?')[0]
        
        # Supabase v2 returns the deleted file info
        result = supabase.storage.from_(PDF_BUCKET).remove([filename])
        
        # Check if operation succeeded
        if isinstance(result, list) and any(f['name'] == filename for f in result):
            return True
        return False
        
    except Exception as e:
        logging.error(f"Delete failed: {str(e)}")
        return False


@router.get("/{lessonfile_id}", response_model=LessonFileRead)
async def get_lesson_pdf(
    lessonfile_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    """Get lesson PDF by ID"""
    lessonfile = await get_lessonfile(db, lessonfile_id)
    if not lessonfile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson file not found"
        )
    return lessonfile

@router.get("/lesson/{lesson_id}", response_model=List[LessonFileRead])
async def get_lesson_pdfs_by_lesson(
    lesson_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    """Get all PDFs for a specific lesson"""
    files = await get_lessonfiles_by_lesson(db, lesson_id)
    return files



@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    from datetime import datetime

    # Validate type
    if not file.content_type or not file.content_type.startswith("application/pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    # Validate size
    max_size = 50 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum size is 50MB"
        )
    file.file.seek(0)

    try:
        pdf_url = await upload_to_supabase(file)
        return {
            "message": "PDF uploaded successfully",
            "pdf_url": pdf_url,
            "filename": file.filename,
            "size": len(contents),
            "uploaded_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during upload: {str(e)}"
        )


@router.post("/", response_model=LessonFileRead, status_code=status.HTTP_201_CREATED)
async def create_lesson_pdf(
    lessonfile_in: LessonFileCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Create a new lesson PDF record in database"""
    try:
        new_file = await create_lessonfile(db, lessonfile_in)
        return new_file
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lesson file record: {str(e)}"
        )


@router.put("/{lessonfile_id}", response_model=LessonFileRead)
async def update_lesson_pdf(
    lessonfile_id: UUID,
    lessonfile_update: LessonFileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update lesson PDF record"""
    lessonfile = await get_lessonfile(db, lessonfile_id)
    if not lessonfile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson file not found"
        )
    
    try:
        updated_file = await update_lessonfile(db, lessonfile_id, lessonfile_update)
        return updated_file
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lesson file: {str(e)}"
        )

@router.delete("/{lessonfile_id}")
async def delete_lesson_pdf(
    lessonfile_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete lesson PDF record and file from Supabase"""
    lessonfile = await get_lessonfile(db, lessonfile_id)
    if not lessonfile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson file not found"
        )
    
    try:
        # Delete from Supabase storage if URL exists
        if lessonfile.file_url:
            await delete_from_supabase(lessonfile.file_url)
        
        # Delete from database
        await delete_lessonfile(db, lessonfile_id)
        
        return {"message": "Lesson PDF deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lesson file: {str(e)}"
        )




from fastapi import Form
from sqlalchemy import update
from app.models import Lesson
import httpx

from app.db.session import get_db


 # change to your agent service URL


@router.post("/upload-and-create")
async def upload_and_create_lesson_pdf(
    file: UploadFile = File(...),
    lesson_id: str = Form(...),
    title: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    if not lesson_id:
        raise ValueError("lesson_id is missing or empty")
    try:
        lesson_id = UUID(lesson_id)
    except ValueError:
        raise HTTPException(400, "Invalid UUID format")

    if not file.content_type or not file.content_type.startswith('application/pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    try:
        # Check if a file already exists
        existing_files = await get_lessonfiles_by_lesson(db, lesson_id)
        existing_file = existing_files[0] if existing_files else None

        # Upload PDF to Supabase
        pdf_url = await upload_to_supabase(file)
        file_data = {
            "lesson_id": lesson_id,
            "filename": title,
            "file_url": pdf_url,
            "file_type": "pdf"
        }

        if existing_file:
            if existing_file.file_url:
                await delete_from_supabase(existing_file.file_url)
            lesson_file_obj = await update_lessonfile(db, existing_file.id, LessonFileUpdate(**file_data))
            action = "updated"
        else:
            lesson_file_obj = await create_lessonfile(db, LessonFileCreate(**file_data))
            action = "created"

        # Update Lesson row pdf column
        await db.execute(update(Lesson).where(Lesson.id == lesson_id).values(pdf=pdf_url))
        await db.commit()

        # ---------------- Trigger Quiz Generation ----------------
        quiz_json = None
        try:
            file_content = await file.read()  # read file once
            async with httpx.AsyncClient() as client:
                response = await client.post(
        f"{AGENT_SERVICE_URL}/upload-quiz",
        files={"pdf": (file.filename, file_content, file.content_type)},
        timeout=60.0
    )

                if response.status_code != 200:
                    content = await response.text()
                    print(f"Agent failed: {response.status_code} - {content}")
                    raise Exception("Agent failed to process PDF")

    # ✅ Async JSON parsing
                print("----------------")
                print(response)
                print("----------------")
                response_bytes = await response.aread()  # async read
                
                print("----------------")
                print(response_bytes)
                print("----------------")
                response_data = json.loads(response_bytes)
                

                print("----------------")
                print(response_data)
                print("----------------")
                quiz_id = response_data.get("quizId")
                if quiz_id:
                    # Fetch quiz JSON from Redis
                    print("-----------------------------------")
                    print("------quiz id",quiz_id)
                    quiz_data = r.get(quiz_id)
                    print("-----------------------------------")
                    if quiz_data:
                        quiz_json = json.loads(quiz_data)
                        # Save quiz JSON in Lesson table
                        await db.execute(
                            update(Lesson).where(Lesson.id == lesson_id).values(quiz_json=quiz_json)
                        )
                        await db.commit()
        except Exception as quiz_error:
            print(f"⚠️ Quiz generation failed: {quiz_error}")

        return {
            "message": f"PDF {action} successfully",
            "lesson_file": lesson_file_obj,
            "pdf_url": pdf_url,
            "quiz": quiz_json,
            "action": action
        }

    except HTTPException:
        raise
    except Exception as e:
        # Clean up newly uploaded PDF on error
        await delete_from_supabase(pdf_url)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process lesson file: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for PDF upload service"""
    try:
        # Test Supabase connection
        buckets = supabase.storage.list_buckets()
        
        return {
            "status": "healthy",
            "supabase_connected": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }