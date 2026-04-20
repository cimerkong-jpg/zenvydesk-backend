"""
Logging helpers for safe and structured logging.
"""
from typing import Optional
import uuid


def mask_token(token: Optional[str], show_chars: int = 6) -> str:
    """
    Mask sensitive token for logging.
    
    Args:
        token: Token to mask
        show_chars: Number of characters to show at start and end
        
    Returns:
        Masked token string
    """
    if not token:
        return "None"
    
    if len(token) <= show_chars * 2:
        return "***"
    
    return f"{token[:show_chars]}...{token[-show_chars:]}"


def mask_session_id(session_id: Optional[str]) -> str:
    """
    Mask session ID for logging.
    
    Args:
        session_id: Session ID to mask
        
    Returns:
        Masked session ID
    """
    return mask_token(session_id, show_chars=4)


def generate_request_id() -> str:
    """
    Generate unique request ID for correlation.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def log_api_call(
    logger,
    action: str,
    method: str,
    url: str,
    status_code: Optional[int] = None,
    success: bool = True,
    error: Optional[str] = None,
    context: Optional[dict] = None
):
    """
    Log API call in structured format.
    
    Args:
        logger: Logger instance
        action: Action name (e.g., "fetch_pages", "publish_post")
        method: HTTP method
        url: API endpoint URL
        status_code: HTTP status code
        success: Whether call succeeded
        error: Error message if failed
        context: Additional context (user_id, page_id, etc.)
    """
    log_data = {
        "action": action,
        "method": method,
        "url": url,
        "status_code": status_code,
        "success": success
    }
    
    if context:
        log_data.update(context)
    
    if success:
        logger.info(f"API call succeeded: {action}", extra=log_data)
    else:
        log_data["error"] = error
        logger.error(f"API call failed: {action}", extra=log_data)


def log_flow_step(
    logger,
    flow: str,
    step: str,
    status: str,
    context: Optional[dict] = None,
    error: Optional[str] = None
):
    """
    Log flow step in structured format.
    
    Args:
        logger: Logger instance
        flow: Flow name (e.g., "facebook_login", "post_to_page")
        step: Step name (e.g., "start", "fetch_pages", "complete")
        status: Status (e.g., "started", "success", "failed")
        context: Additional context
        error: Error message if failed
    """
    log_data = {
        "flow": flow,
        "step": step,
        "status": status
    }
    
    if context:
        log_data.update(context)
    
    if status == "failed" and error:
        log_data["error"] = error
        logger.error(f"Flow step failed: {flow}.{step}", extra=log_data)
    elif status == "started":
        logger.info(f"Flow step started: {flow}.{step}", extra=log_data)
    else:
        logger.info(f"Flow step completed: {flow}.{step}", extra=log_data)
