"""
AI Content Generation Routes.
Orchestrates AI content generation without mixing with Facebook posting logic.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ai_bot_adapter import ai_bot_adapter
from app.services.draft_service import DraftService
from app.models.content_draft import DraftSource
from app.schemas.ai_content import AIGenerateRequest, AIGenerateResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ai")


def get_user_from_session(session_id: str, db: Session) -> int:
    """
    Helper to get user_id from session_id.
    Reuses existing session architecture.
    """
    from app.services.session_service import SessionService
    from app.models.login_session import LoginSession
    from app.config import settings
    from datetime import datetime, timedelta
    
    login_session = db.query(LoginSession).filter(
        LoginSession.session_id == session_id,
        LoginSession.status == "success"
    ).first()
    
    if not login_session or not login_session.user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Check if session has expired
    expiry_time = login_session.updated_at + timedelta(minutes=settings.SESSION_EXPIRY_MINUTES)
    if datetime.utcnow() > expiry_time:
        logger.warning(f"Session {session_id} has expired")
        raise HTTPException(status_code=401, detail="Session has expired. Please login again")
    
    return login_session.user_id


@router.post("/generate", response_model=AIGenerateResponse)
async def generate_content(
    request: AIGenerateRequest,
    session_id: str = Query(..., description="Session ID from login flow"),
    db: Session = Depends(get_db)
):
    """
    Generate AI content using BOT_PAPE.
    
    This endpoint:
    1. Validates user session
    2. Calls BOT_PAPE to generate content
    3. Returns generated content for user review/edit
    4. Does NOT post to Facebook (user must approve first)
    
    Args:
        request: Content generation request
        session_id: Session ID from successful login
        db: Database session
        
    Returns:
        Generated content and metadata
    """
    try:
        # Validate session
        user_id = get_user_from_session(session_id, db)
        
        logger.info(f"[AI Generate] User {user_id} requesting content - type: {request.content_type}")
        
        # Check if BOT_PAPE is available
        if not ai_bot_adapter.is_available():
            logger.error("[AI Generate] BOT_PAPE not available")
            return AIGenerateResponse(
                success=False,
                error="AI content generation service is not available. Please contact support."
            )
        
        # Build product context if provided
        product_context = None
        if request.product_name or request.product_category:
            product_context = {
                "name": request.product_name or "",
                "category": request.product_category or "",
                "description": request.product_description or "",
                "selling_points": []  # Could be extended later
            }
            logger.info(f"[AI Generate] Using product context: {request.product_name}")
        
        # Generate content via BOT_PAPE
        result = await ai_bot_adapter.generate_content(
            prompt=request.prompt,
            content_type=request.content_type,
            product_context=product_context
        )
        
        if result["success"]:
            # Save draft
            draft = DraftService.create_draft(
                db=db,
                user_id=user_id,
                content=result["content"],
                source=DraftSource.AI,
                content_type=request.content_type,
                product_name=request.product_name,
                product_category=request.product_category
            )
            
            logger.info(f"[AI Generate] Success for user {user_id} - {result['metadata'].get('length', 0)} chars, draft_id: {draft.id}")
            
            return AIGenerateResponse(
                success=True,
                content=result["content"],
                draft_id=draft.id,
                metadata=result.get("metadata")
            )
        else:
            logger.warning(f"[AI Generate] Failed for user {user_id}: {result.get('error')}")
            
            return AIGenerateResponse(
                success=False,
                error=result.get("error")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AI Generate] Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@router.get("/status")
async def ai_status(
    session_id: str = Query(..., description="Session ID from login flow"),
    db: Session = Depends(get_db)
):
    """
    Check AI service status.
    
    Args:
        session_id: Session ID from successful login
        db: Database session
        
    Returns:
        AI service availability status
    """
    try:
        # Validate session
        user_id = get_user_from_session(session_id, db)
        
        # Check BOT_PAPE availability
        is_available = ai_bot_adapter.is_available()
        
        return {
            "available": is_available,
            "service": "BOT_PAPE/ContentEngine",
            "status": "ready" if is_available else "unavailable"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AI Status] Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check AI status")
