"""
Application configuration management.
Loads settings from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "ZenvyDesk API"
    APP_ENV: str = "development"
    APP_BASE_URL: str = "https://api.zenvydesk.site"
    FRONTEND_BASE_URL: str = "https://zenvydesk.site"
    
    # Facebook OAuth
    FACEBOOK_APP_ID: str
    FACEBOOK_APP_SECRET: str
    FACEBOOK_REDIRECT_URI: str = "https://api.zenvydesk.site/auth/facebook/callback"
    FACEBOOK_SCOPES: str = "public_profile,email"
    
    # Database
    DATABASE_URL: str = "sqlite:///./zenvydesk.db"
    
    # Session
    SESSION_EXPIRY_MINUTES: int = 15
    
    # AI Bot Integration
    BOT_PAPE_PATH: Optional[str] = None  # Path to BOT_PAPE/fb-bot folder, if None will auto-discover
    
    # Security
    SECRET_KEY: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
