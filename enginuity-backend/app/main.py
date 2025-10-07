from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routers import health, notes, search, quiz, chat, export, upload

settings = get_settings()
app = FastAPI(title="Enginuity Backend", version="0.1.0")

# CORS
origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])

