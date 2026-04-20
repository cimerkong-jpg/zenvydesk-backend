"""
Pydantic schemas for AI content generation endpoints.
"""
from pydantic import BaseModel, validator
from typing import Optional, Dict


class AIGenerateRequest(BaseModel):
    """Request to generate AI content."""
    prompt: str
    content_type: Optional[str] = "sale"  # morning, sale, evening
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    product_description: Optional[str] = None
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty')
        if len(v) > 1000:
            raise ValueError('Prompt too long (max 1000 characters)')
        return v.strip()
    
    @validator('content_type')
    def validate_content_type(cls, v):
        if v not in ['morning', 'sale', 'evening']:
            raise ValueError('content_type must be: morning, sale, or evening')
        return v


class AIGenerateResponse(BaseModel):
    """Response from AI content generation."""
    success: bool
    content: Optional[str] = None
    draft_id: Optional[int] = None  # ID of saved draft
    error: Optional[str] = None
    metadata: Optional[Dict] = None
