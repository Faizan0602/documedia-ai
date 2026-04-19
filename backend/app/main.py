from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # ✅ Import StaticFiles for serving media

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.routes import upload
from app.api.routes import chat, health, summary, timestamps


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health")
app.include_router(upload.router, prefix="/api/v1/upload")
app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(summary.router, prefix="/api/v1/summary", tags=["Summary"])
app.include_router(timestamps.router, prefix="/api/v1/timestamps", tags=["Timestamps"])

# ✅ Mount the uploads directory so React can play the videos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")