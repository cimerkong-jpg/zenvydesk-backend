"""
Pydantic schemas for content draft endpoints.
"""
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime


class DraftInfo(BaseModel):
    """Content draft information."""
    id: int
    user_id: int
    source: str  # ai, manual
    content: str
    content_type: Optional[str] = None
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    status: str  # generated, edited, approved, posted, failed
    selected_page_id: Optional[int] = None
    post_history_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DraftListResponse(BaseModel):
    """Response with list of drafts."""
    drafts: List[DraftInfo]
    total: int
    page: int
    page_size: int


class DraftUpdateRequest(BaseModel):
    """Request to update draft content."""
    content: str
    selected_page_id: Optional[int] = None
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > 5000:
            raise ValueError('Content too long (max 5000 characters)')
        return v.strip()


class DraftPostRequest(BaseModel):
    """Request to post draft to Facebook."""
    draft_id: int
    page_id: Optional[int] = None  # Override selected_page_id if provided
