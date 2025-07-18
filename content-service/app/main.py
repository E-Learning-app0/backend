# app/main.py
from fastapi import FastAPI
from app.routers import lessons  # import your lessons router
from app.routers import modules  # import your lessons router

app = FastAPI()

app.include_router(modules.router)

# Add init_db call on startup if you want table creation at launch
