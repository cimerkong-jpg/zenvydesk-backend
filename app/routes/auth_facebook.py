"""
Facebook OAuth authentication routes.
"""
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.facebook_oauth_service import FacebookOAuthService
from app.services.user_service import UserService
from app.services.session_service import SessionService
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth/facebook")
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
async def facebook_login(
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Initiate Facebook OAuth login flow.
    
    Args:
        session_id: Optional session ID from desktop app
        db: Database session
        
    Returns:
        Redirect to Facebook OAuth dialog
    """
    try:
        # Create login session
        login_session = SessionService.create_login_session(db, session_id)
        
        # Generate Facebook OAuth URL
        auth_url = FacebookOAuthService.get_authorization_url(login_session.oauth_state)
        
        logger.info(f"Redirecting to Facebook OAuth for session: {login_session.session_id}")
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Error initiating Facebook login: {str(e)}")
        return HTMLResponse(
            content="<h1>Error</h1><p>Failed to initiate login. Please try again.</p>",
            status_code=500
        )


@router.get("/callback")
async def facebook_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handle Facebook OAuth callback.
    
    Args:
        request: FastAPI request object
        code: Authorization code from Facebook
        state: OAuth state parameter
        error: Error code if OAuth failed
        error_description: Error description if OAuth failed
        db: Database session
        
    Returns:
        HTML response (success or error page)
    """
    # Handle OAuth error
    if error:
        logger.warning(f"Facebook OAuth error: {error} - {error_description}")
        return templates.TemplateResponse(
            "auth_error.html",
            {
                "request": request,
                "error_message": error_description or "Authentication failed"
            }
        )
    
    # Validate required parameters
    if not code or not state:
        logger.error("Missing code or state in callback")
        return templates.TemplateResponse(
            "auth_error.html",
            {
                "request": request,
                "error_message": "Invalid callback parameters"
            }
        )
    
    try:
        # Validate state and get login session
        login_session = SessionService.get_session_by_state(db, state)
        
        if not login_session:
            logger.error(f"Invalid OAuth state: {state}")
            return templates.TemplateResponse(
                "auth_error.html",
                {
                    "request": request,
                    "error_message": "Invalid or expired session"
                }
            )
        
        # Exchange code for access token
        token_data = await FacebookOAuthService.exchange_code_for_token(code)
        
        if not token_data:
            SessionService.mark_session_failed(db, login_session, "Failed to exchange code for token")
            return templates.TemplateResponse(
                "auth_error.html",
                {
                    "request": request,
                    "error_message": "Failed to authenticate with Facebook"
                }
            )
        
        access_token = token_data.get("access_token")
        token_type = token_data.get("token_type", "bearer")
        expires_in = token_data.get("expires_in")
        
        # Get user info from Facebook
        fb_user_info = await FacebookOAuthService.get_user_info(access_token)
        
        if not fb_user_info:
            SessionService.mark_session_failed(db, login_session, "Failed to fetch user info")
            return templates.TemplateResponse(
                "auth_error.html",
                {
                    "request": request,
                    "error_message": "Failed to retrieve user information"
                }
            )
        
        # Create or update user
        user = UserService.get_or_create_user_from_facebook(
            db, fb_user_info, access_token, token_type, expires_in
        )
        
        # Mark session as successful
        SessionService.mark_session_success(db, login_session, user)
        
        logger.info(f"Successfully authenticated user {user.id} via Facebook")
        
        return templates.TemplateResponse(
            "auth_success.html",
            {
                "request": request,
                "user_name": user.name or "User"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in Facebook callback: {str(e)}")
        
        # Try to mark session as failed if we have it
        try:
            if 'login_session' in locals():
                SessionService.mark_session_failed(db, login_session, str(e))
        except:
            pass
        
        return templates.TemplateResponse(
            "auth_error.html",
            {
                "request": request,
                "error_message": "An unexpected error occurred"
            }
        )
