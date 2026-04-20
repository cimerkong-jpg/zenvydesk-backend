"""
Pydantic schemas for Facebook Pages endpoints.
"""
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class FacebookPageInfo(BaseModel):
    """Facebook Page information."""
    id: int
    facebook_page_id: str
    page_name: str
    category: Optional[str] = None
    is_selected: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PageSelectionRequest(BaseModel):
    """Request to select a page."""
    page_id: int


class PagePostRequest(BaseModel):
    """Request to post to a page."""
    page_id: Optional[int] = None  # If None, use selected page
    message: str
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 63206:  # Facebook's limit for page posts
            raise ValueError('Message exceeds Facebook limit of 63206 characters')
        return v.strip()


class PagePostResponse(BaseModel):
    """Response after posting to a page."""
    success: bool
    post_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class PagesListResponse(BaseModel):
    """Response with list of pages."""
    pages: list[FacebookPageInfo]
    selected_page_id: Optional[int] = None
