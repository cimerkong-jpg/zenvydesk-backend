"""
Facebook OAuth service for handling OAuth flow and API interactions.
"""
import httpx
from typing import Dict, Optional
from app.config import settings
from app.utils.logging import get_logger
from app.schemas.auth import FacebookUserInfo

logger = get_logger(__name__)


class FacebookOAuthService:
    """Service for Facebook OAuth operations."""
    
    OAUTH_DIALOG_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
    USER_INFO_URL = "https://graph.facebook.com/v18.0/me"
    
    @staticmethod
    def get_authorization_url(state: str) -> str:
        """
        Generate Facebook OAuth authorization URL.
        
        Args:
            state: OAuth state parameter for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "state": state,
            "scope": "public_profile",
            "response_type": "code"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{FacebookOAuthService.OAUTH_DIALOG_URL}?{query_string}"
        
        logger.info(f"Generated Facebook OAuth URL with state")
        return url
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> Optional[Dict[str, any]]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from Facebook
            
        Returns:
            Token response dict or None if failed
        """
        params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "code": code
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(FacebookOAuthService.TOKEN_URL, params=params)
                response.raise_for_status()
                token_data = response.json()
                
                logger.info("Successfully exchanged code for access token")
                return token_data
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to exchange code for token: {str(e)}")
            return None
    
    @staticmethod
    async def get_user_info(access_token: str) -> Optional[FacebookUserInfo]:
        """
        Fetch user information from Facebook Graph API.
        
        Args:
            access_token: Facebook access token
            
        Returns:
            FacebookUserInfo object or None if failed
        """
        params = {
            "fields": "id,name",
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(FacebookOAuthService.USER_INFO_URL, params=params)
                response.raise_for_status()
                user_data = response.json()
                
                logger.info(f"Successfully fetched user info for Facebook user ID: {user_data.get('id')}")
                return FacebookUserInfo(**user_data)
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch user info: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing user info: {str(e)}")
            return None
