# app/main.py
from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Transcript Improver")
# Keep it simple for Stage 1: no version prefix
app.include_router(router)
