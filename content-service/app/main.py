# app/main.py
from fastapi import FastAPI
from app.routers import lessons  # import your lessons router
from app.routers import modules  # import your lessons router
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users_progress, user_lesson_progress

app = FastAPI()

origins = [
    "http://localhost:5173",  
    "https://frontend-five-pi-35.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,
    allow_methods=["*"],              
    allow_headers=["*"],              
)

app.include_router(lessons.router)
app.include_router(modules.router)
app.include_router(users_progress.router)
app.include_router(user_lesson_progress.router)