# app/core/quiz_config.py
import os

class QuizConfig:
    # Quiz microservice URL
    QUIZ_MICROSERVICE_URL = os.getenv("QUIZ_MICROSERVICE_URL", "http://localhost:8002/upload-quiz")
    
    # Background task configuration - 24 hours for production
    QUIZ_GENERATION_INTERVAL_HOURS = float(os.getenv("QUIZ_GENERATION_INTERVAL_HOURS", "24"))  # 24 hours
    
    # HTTP request timeout
    HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))
    
    # PDF base URL - configure this to match where your PDFs are hosted
    PDF_BASE_URL = os.getenv("PDF_BASE_URL", "http://localhost:8080/static/pdfs/")  # Adjust this URL

quiz_config = QuizConfig()
