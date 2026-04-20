"""
Facebook OAuth service for handling OAuth flow and API interactions.
"""
import httpx
from typing import Dict, Optional, List
from app.config import settings
from app.utils.logging import get_logger
from app.utils.log_helpers import mask_token, log_api_call
from app.schemas.auth import FacebookUserInfo

logger = get_logger(__name__)


class FacebookOAuthService:
    """Service for Facebook OAuth operations."""
    
    OAUTH_DIALOG_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
    USER_INFO_URL = "https://graph.facebook.com/v18.0/me"
    PAGES_URL = "https://graph.facebook.com/v18.0/me/accounts"
    
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
            "scope": "public_profile,pages_show_list,pages_read_engagement,pages_manage_posts",
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
    
    @staticmethod
    async def fetch_managed_pages(access_token: str) -> Optional[List[Dict]]:
        """
        Fetch Facebook Pages that the user manages.
        
        Args:
            access_token: User's Facebook access token
            
        Returns:
            List of page data dicts or None if failed
        """
        masked_token = mask_token(access_token)
        logger.info(f"[fetch_managed_pages] Starting - token: {masked_token}")
        
        params = {
            "fields": "id,name,access_token,category,tasks",
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(FacebookOAuthService.PAGES_URL, params=params)
                response.raise_for_status()
                pages_data = response.json()
                
                pages = pages_data.get("data", [])
                
                log_api_call(
                    logger,
                    action="fetch_managed_pages",
                    method="GET",
                    url=FacebookOAuthService.PAGES_URL,
                    status_code=response.status_code,
                    success=True,
                    context={"pages_count": len(pages), "token_masked": masked_token}
                )
                
                return pages
                
        except httpx.HTTPStatusError as e:
            error_body = e.response.text if hasattr(e.response, 'text') else str(e)
            
            log_api_call(
                logger,
                action="fetch_managed_pages",
                method="GET",
                url=FacebookOAuthService.PAGES_URL,
                status_code=e.response.status_code,
                success=False,
                error=error_body,
                context={"token_masked": masked_token}
            )
            return None
            
        except httpx.HTTPError as e:
            logger.error(f"[fetch_managed_pages] HTTP error: {str(e)}, token: {masked_token}")
            return None
        except Exception as e:
            logger.error(f"[fetch_managed_pages] Unexpected error: {str(e)}, token: {masked_token}")
            return None
    
    @staticmethod
    async def publish_page_post(page_id: str, page_access_token: str, message: str) -> Optional[Dict]:
        """
        Publish a text post to a Facebook Page.
        
        Args:
            page_id: Facebook Page ID
            page_access_token: Page access token
            message: Text message to post
            
        Returns:
            Post response dict with post_id or None if failed
        """
        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
        masked_token = mask_token(page_access_token)
        message_preview = message[:50] + "..." if len(message) > 50 else message
        
        logger.info(f"[publish_page_post] Starting - page_id: {page_id}, token: {masked_token}, message_length: {len(message)}")
        
        data = {
            "message": message,
            "access_token": page_access_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                post_data = response.json()
                
                post_id = post_data.get("id")
                
                log_api_call(
                    logger,
                    action="publish_page_post",
                    method="POST",
                    url=url,
                    status_code=response.status_code,
                    success=True,
                    context={
                        "page_id": page_id,
                        "post_id": post_id,
                        "message_length": len(message),
                        "message_preview": message_preview,
                        "token_masked": masked_token
                    }
                )
                
                return post_data
                
        except httpx.HTTPStatusError as e:
            error_body = e.response.text if hasattr(e.response, 'text') else str(e)
            
            log_api_call(
                logger,
                action="publish_page_post",
                method="POST",
                url=url,
                status_code=e.response.status_code,
                success=False,
                error=error_body,
                context={
                    "page_id": page_id,
                    "message_length": len(message),
                    "token_masked": masked_token
                }
            )
            return None
            
        except httpx.HTTPError as e:
            logger.error(f"[publish_page_post] HTTP error: {str(e)}, page_id: {page_id}, token: {masked_token}")
            return None
        except Exception as e:
            logger.error(f"[publish_page_post] Unexpected error: {str(e)}, page_id: {page_id}, token: {masked_token}")
            return None
