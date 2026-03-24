from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import generation, turnaround

app = FastAPI(
    title="Spritify API",
    description="Generate sprite sheets from static images using AI",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/outputs", exist_ok=True)
os.makedirs("static/turnarounds", exist_ok=True)
os.makedirs("static/frames", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routes
app.include_router(generation.router, prefix="/api/v1", tags=["generation"])
app.include_router(turnaround.router, prefix="/api/v1", tags=["turnaround"])


@app.get("/")
async def root():
    return {"message": "Spritify API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
