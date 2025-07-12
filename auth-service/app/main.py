from fastapi import FastAPI
from app.api.v1.routes import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:5173",  # or the actual URL where your React app runs
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # allow only your frontend origin(s)
    allow_credentials=True,
    allow_methods=["*"],              # allow all HTTP methods
    allow_headers=["*"],              # allow all headers
)


app.include_router(auth_router, prefix="/api/v1")
