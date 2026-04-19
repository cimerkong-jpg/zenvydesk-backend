"""
Data deletion endpoint for Meta compliance.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import DataDeletionRequest, DataDeletionResponse
from app.utils.security import generate_secure_token
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth/facebook")


@router.post("/data-deletion", response_model=DataDeletionResponse)
async def handle_data_deletion(
    request: DataDeletionRequest,
    db: Session = Depends(get_db)
):
    """
    Handle Facebook data deletion callback.
    
    This endpoint is required by Meta for app review.
    It receives deletion requests and returns a confirmation URL and code.
    
    Args:
        request: Data deletion request with signed_request
        db: Database session
        
    Returns:
        DataDeletionResponse with confirmation URL and code
    """
    try:
        # Generate unique confirmation code
        confirmation_code = generate_secure_token(16)
        
        # TODO: Implement actual data deletion logic
        # For MVP, we acknowledge the request and provide a tracking mechanism
        # In production, you should:
        # 1. Parse and validate the signed_request
        # 2. Extract user_id from the signed_request
        # 3. Queue the deletion request for processing
        # 4. Delete user data according to your data retention policy
        # 5. Store the confirmation_code for status tracking
        
        logger.info(f"Data deletion request received with confirmation code: {confirmation_code}")
        
        # Return confirmation URL where user can check deletion status
        confirmation_url = f"{settings.FRONTEND_BASE_URL}/data-deletion?code={confirmation_code}"
        
        return DataDeletionResponse(
            url=confirmation_url,
            confirmation_code=confirmation_code
        )
        
    except Exception as e:
        logger.error(f"Error handling data deletion request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process deletion request")
