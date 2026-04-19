"""
Security utilities for token generation and validation.
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes (default 32)
        
    Returns:
        Hex-encoded secure random token
    """
    return secrets.token_urlsafe(length)


def generate_oauth_state() -> str:
    """
    Generate a secure OAuth state parameter.
    
    Returns:
        Secure random state string
    """
    return generate_secure_token(32)


def hash_token(token: str) -> str:
    """
    Create a SHA-256 hash of a token for safe storage.
    
    Args:
        token: Token to hash
        
    Returns:
        Hex-encoded hash
    """
    return hashlib.sha256(token.encode()).hexdigest()


def is_expired(timestamp: datetime, expiry_minutes: int) -> bool:
    """
    Check if a timestamp has expired.
    
    Args:
        timestamp: The timestamp to check
        expiry_minutes: Number of minutes until expiration
        
    Returns:
        True if expired, False otherwise
    """
    expiry_time = timestamp + timedelta(minutes=expiry_minutes)
    return datetime.utcnow() > expiry_time
