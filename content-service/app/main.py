# app/main.py
from fastapi import FastAPI
from app.routers import lessons  # import your lessons router
from app.routers import modules  # import your lessons router
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users_progress
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

app.include_router(users_progress.router)

# Add init_db call on startup if you want table creation at launch
