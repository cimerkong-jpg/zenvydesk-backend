"""
ZenvyDesk API - Main application entry point.

An AI-powered desktop tool backend that supports Facebook OAuth login
for secure user authentication. All actions are user-initiated and controlled.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.db.base import init_db
from app.utils.logging import setup_logging, get_logger
from app.routes import health, auth_facebook, auth_session, data_deletion, facebook_pages, post_history, ai_content, content_drafts

# Setup logging
setup_logging(app_name="ZenvyDesk", level="INFO" if settings.APP_ENV == "production" else "DEBUG")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode")
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for ZenvyDesk - An AI-powered desktop tool for content creation and workflow assistance",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_BASE_URL,
        "http://localhost:3000",  # For local development
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth_facebook.router, tags=["Authentication"])
app.include_router(auth_session.router, tags=["Session"])
app.include_router(data_deletion.router, tags=["Data Deletion"])
app.include_router(facebook_pages.router, tags=["Facebook Pages"])
app.include_router(post_history.router, tags=["Post History"])
app.include_router(ai_content.router, tags=["AI Content"])
app.include_router(content_drafts.router, tags=["Content Drafts"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Use PORT from environment (for Render/Heroku) or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.APP_ENV == "development"
    )
