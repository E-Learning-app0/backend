# app/services/quiz_background_service.py
import asyncio
import logging
import httpx
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.models.lesson import Lesson
from app.db.session import get_db
from app.core.quiz_config import quiz_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuizBackgroundService:
    def __init__(self):
        self.is_running = False
        
    async def call_quiz_microservice(self, pdf_url: str) -> Optional[str]:
        """Call the external quiz microservice to generate quiz from PDF"""
        try:
            # Handle different PDF path formats
            if pdf_url.startswith(('http://', 'https://')):
                # Already a full URL
                full_pdf_url = pdf_url
                logger.info(f"Using full PDF URL: {full_pdf_url}")
                print(f"🌐 Using full PDF URL: {full_pdf_url}")
            elif pdf_url.startswith(('C:', 'D:', '/', '\\')):
                # Local file path - try to read directly
                logger.info(f"Detected local file path: {pdf_url}")
                print(f"📁 Detected local file path: {pdf_url}")
                try:
                    with open(pdf_url, 'rb') as f:
                        pdf_content = f.read()
                    logger.info(f"Read local PDF file, size: {len(pdf_content)} bytes")
                    print(f"✅ Read local PDF file, size: {len(pdf_content)} bytes")
                    
                    # Skip download step and go directly to quiz generation
                    return await self._send_pdf_to_quiz_service(pdf_content, pdf_url)
                except FileNotFoundError:
                    logger.error(f"Local PDF file not found: {pdf_url}")
                    print(f"❌ Local PDF file not found: {pdf_url}")
                    return None
                except Exception as e:
                    logger.error(f"Error reading local PDF file {pdf_url}: {str(e)}")
                    print(f"❌ Error reading local PDF: {str(e)}")
                    return None
            else:
                # Relative filename - construct URL
                full_pdf_url = quiz_config.PDF_BASE_URL + pdf_url.lstrip('/')
                logger.info(f"Converted relative PDF path '{pdf_url}' to full URL: {full_pdf_url}")
                print(f"📁 Converting PDF path: {pdf_url} → {full_pdf_url}")
            
            # Download the PDF content from URL
            async with httpx.AsyncClient(timeout=quiz_config.HTTP_TIMEOUT_SECONDS) as client:
                logger.info(f"Downloading PDF from: {full_pdf_url}")
                print(f"⬇️ Downloading PDF from: {full_pdf_url}")
                pdf_response = await client.get(full_pdf_url)
                if pdf_response.status_code != 200:
                    logger.error(f"Failed to download PDF from {full_pdf_url} - Status: {pdf_response.status_code}")
                    print(f"❌ Failed to download PDF - Status: {pdf_response.status_code}")
                    return None
                
                pdf_content = pdf_response.content
                logger.info(f"Downloaded PDF content, size: {len(pdf_content)} bytes")
                print(f"✅ Downloaded PDF, size: {len(pdf_content)} bytes")
                
                return await self._send_pdf_to_quiz_service(pdf_content, pdf_url)
                    
        except Exception as e:
            logger.error(f"Error calling quiz microservice for PDF {pdf_url}: {str(e)}")
            print(f"❌ Error with PDF {pdf_url}: {str(e)}")
            return None
    
    async def _send_pdf_to_quiz_service(self, pdf_content: bytes, original_path: str) -> Optional[str]:
        """Send PDF content to quiz microservice"""
        try:
            async with httpx.AsyncClient(timeout=quiz_config.HTTP_TIMEOUT_SECONDS) as client:
                # Prepare the file for upload to quiz microservice
                files = {"pdf": ("lesson.pdf", pdf_content, "application/pdf")}
                
                # Call quiz generation microservice
                logger.info(f"Calling quiz microservice at: {quiz_config.QUIZ_MICROSERVICE_URL}")
                print(f"🔗 Calling quiz microservice...")
                quiz_response = await client.post(quiz_config.QUIZ_MICROSERVICE_URL, files=files)
                
                if quiz_response.status_code == 200:
                    quiz_data = quiz_response.json()
                    quiz_id = quiz_data.get("quizId")
                    if quiz_id:
                        logger.info(f"🎉 SUCCESS! Generated quiz with ID: {quiz_id} for PDF: {original_path}")
                        print(f"🎉 QUIZ GENERATED: {quiz_id}")
                        return quiz_id
                    else:
                        logger.error("Quiz microservice returned invalid response - no quizId")
                        print("❌ Quiz microservice returned invalid response")
                        return None
                else:
                    logger.error(f"Quiz microservice returned status {quiz_response.status_code} - Response: {quiz_response.text}")
                    print(f"❌ Quiz microservice error - Status: {quiz_response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error sending PDF to quiz service: {type(e).__name__}: {str(e)}")
            print(f"❌ Error sending PDF to quiz service: {type(e).__name__}: {str(e)}")
            # Add more detailed error information
            if hasattr(e, 'response'):
                logger.error(f"HTTP Response: {e.response.status_code if hasattr(e.response, 'status_code') else 'Unknown'}")
                print(f"📊 HTTP Response code: {e.response.status_code if hasattr(e.response, 'status_code') else 'Unknown'}")
            if hasattr(e, '__traceback__'):
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    async def get_lessons_without_quiz(self, db: AsyncSession):
        """Get all lessons that have PDF content (including those with existing quiz_id for regeneration)"""
        try:
            stmt = select(Lesson).where(
                Lesson.pdf.isnot(None),
                Lesson.pdf != ''
            )
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting lessons with PDF: {str(e)}")
            return []
    
    async def update_lesson_quiz_id(self, db: AsyncSession, lesson_id, quiz_id: str):
        """Update lesson with the generated quiz_id"""
        try:
            stmt = update(Lesson).where(Lesson.id == lesson_id).values(quiz_id=quiz_id)
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating lesson {lesson_id} with quiz_id: {str(e)}")
            return False
    
    async def process_lessons_for_quiz_generation(self):
        """Process all lessons that need quiz generation"""
        try:
            async for db in get_db():
                try:
                    # Get all lessons with PDFs (including those with existing quiz_ids)
                    lessons = await self.get_lessons_without_quiz(db)
                    logger.info(f"📚 Found {len(lessons)} lessons with PDFs to process for quiz generation/regeneration")
                    print(f"📚 Found {len(lessons)} lessons with PDFs (including existing quiz_ids)")
                    
                    if len(lessons) == 0:
                        logger.info("✅ No lessons with PDFs found!")
                        print("✅ No lessons with PDFs found!")
                    
                    for lesson in lessons:
                        try:
                            existing_quiz_status = "🔄 UPDATING" if lesson.quiz_id else "🆕 CREATING"
                            logger.info(f"Processing lesson {lesson.id}: {lesson.title} ({existing_quiz_status})")
                            print(f"{existing_quiz_status} quiz for: {lesson.title}")
                            
                            # Generate quiz using microservice
                            quiz_id = await self.call_quiz_microservice(lesson.pdf)
                            
                            if quiz_id:
                                # Update lesson with new quiz_id (overwrites existing if present)
                                success = await self.update_lesson_quiz_id(db, lesson.id, quiz_id)
                                if success:
                                    if lesson.quiz_id:
                                        logger.info(f"🔄 Successfully UPDATED lesson {lesson.id} with NEW quiz_id: {quiz_id} (replaced old: {lesson.quiz_id})")
                                        print(f"🔄 UPDATED: {lesson.title} → NEW Quiz ID: {quiz_id}")
                                    else:
                                        logger.info(f"✅ Successfully CREATED quiz for lesson {lesson.id} with quiz_id: {quiz_id}")
                                        print(f"✅ CREATED: {lesson.title} → Quiz ID: {quiz_id}")
                                else:
                                    logger.error(f"❌ Failed to update lesson {lesson.id} in database")
                            else:
                                logger.warning(f"⚠️ Failed to generate quiz for lesson {lesson.id}: {lesson.title}")
                                
                        except Exception as e:
                            logger.error(f"Error processing lesson {lesson.id}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error in quiz generation process: {str(e)}")
                finally:
                    await db.close()
                break  # Only need one iteration of the async generator
                
        except Exception as e:
            logger.error(f"Error in process_lessons_for_quiz_generation: {str(e)}")
    
    async def start_background_task(self):
        """Start the background task that runs every 3 minutes"""
        if self.is_running:
            logger.warning("Background quiz generation task is already running")
            return
            
        self.is_running = True
        logger.info("🚀 Starting background quiz generation task (3-minute intervals for testing)")
        print("🚀 Background quiz generation task started - checking every 3 minutes")
        
        try:
            # Run immediately on startup
            logger.info("🔄 Running initial quiz generation check...")
            print("🔄 Running initial quiz generation check...")
            await self.process_lessons_for_quiz_generation()
            
            # Then run every 3 minutes
            while True:
                task_interval = quiz_config.QUIZ_GENERATION_INTERVAL_HOURS * 60 * 60  # Convert hours to seconds
                logger.info(f"⏰ Quiz generation completed. Waiting {task_interval} seconds ({quiz_config.QUIZ_GENERATION_INTERVAL_HOURS} hours) for next run...")
                print(f"⏰ Next check in {task_interval} seconds ({quiz_config.QUIZ_GENERATION_INTERVAL_HOURS} hours)")
                
                # Wait for configured interval before next run
                await asyncio.sleep(task_interval)
                
                # Run the next check
                logger.info("🔄 Running quiz generation for lessons...")
                print("🔄 Starting quiz generation check...")
                await self.process_lessons_for_quiz_generation()
                
        except asyncio.CancelledError:
            logger.info("Background quiz generation task cancelled")
            print("🛑 Background quiz generation task cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in background task: {str(e)}")
            print(f"❌ Error in background task: {str(e)}")
        finally:
            self.is_running = False
            logger.info("Background quiz generation task stopped")
            print("🛑 Background quiz generation task stopped")
    
    async def process_now(self):
        """Process lessons immediately (for manual trigger)"""
        if self.is_running:
            logger.warning("Background task is already running, skipping manual process")
            return False
            
        try:
            await self.process_lessons_for_quiz_generation()
            return True
        except Exception as e:
            logger.error(f"Error in manual process: {str(e)}")
            return False

# Global instance
quiz_background_service = QuizBackgroundService()
