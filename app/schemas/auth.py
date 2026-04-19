"""
Pydantic schemas for authentication endpoints.
"""
from pydantic import BaseModel
from typing import Optional


class FacebookUserInfo(BaseModel):
    """Facebook user information from Graph API."""
    id: str
    name: Optional[str] = None
    email: Optional[str] = None


class LoginSessionResponse(BaseModel):
    """Response for login session status."""
    status: str  # pending, success, failed, expired
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    error_message: Optional[str] = None


class DataDeletionRequest(BaseModel):
    """Request payload for data deletion callback."""
    signed_request: str


class DataDeletionResponse(BaseModel):
    """Response for data deletion request."""
    url: str
    confirmation_code: str
