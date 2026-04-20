"""
Pydantic schemas for post history endpoints.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PostHistoryInfo(BaseModel):
    """Post history information."""
    id: int
    user_id: int
    page_id: int
    facebook_page_id: str
    page_name: str
    content: str
    status: str  # pending, success, failed
    facebook_post_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PostHistoryListResponse(BaseModel):
    """Response with list of post history."""
    posts: List[PostHistoryInfo]
    total: int
    page: int
    page_size: int
