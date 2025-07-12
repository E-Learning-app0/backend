from fastapi import FastAPI
from app.api.v1.routes import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

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


app.include_router(auth_router, prefix="/api/v1")
