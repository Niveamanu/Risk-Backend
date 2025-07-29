from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests
import json
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()

class AzureAuthMiddleware:
    def __init__(self):
        from config import AzureConfig
        
        # Azure AD configuration from config
        self.tenant_id = AzureConfig.TENANT_ID
        self.client_id = AzureConfig.CLIENT_ID
        
        # Use the correct issuer format for your token
        self.issuer = f"https://sts.windows.net/{self.tenant_id}/"
        self.jwks_url = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
        
        # Cache for JWKS (JSON Web Key Set)
        self.jwks_cache = None
        self.jwks_cache_time = None
    
    def get_jwks(self) -> Dict[str, Any]:
        """Fetch and cache the JSON Web Key Set from Azure AD"""
        try:
            response = requests.get(self.jwks_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching JWKS: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to verify token"
            )
    
    def get_signing_key(self, token: str) -> str:
        """Get the appropriate signing key for the token"""
        try:
            # Decode the header without verification to get the key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")
            
            if not key_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format"
                )
            
            # Get JWKS
            jwks = self.get_jwks()
            
            # Find the key with matching key ID
            for key in jwks.get("keys", []):
                if key.get("kid") == key_id:
                    # Convert the key to the format expected by python-jose
                    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
                    from cryptography.hazmat.primitives.asymmetric import rsa
                    from cryptography.hazmat.backends import default_backend
                    import base64
                    
                    # Extract the modulus and exponent
                    n = int.from_bytes(base64.urlsafe_b64decode(key['n'] + '=='), byteorder='big')
                    e = int.from_bytes(base64.urlsafe_b64decode(key['e'] + '=='), byteorder='big')
                    
                    # Create the public key
                    public_numbers = RSAPublicNumbers(e, n)
                    public_key = public_numbers.public_key(backend=default_backend())
                    
                    return public_key
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature"
            )
            
        except Exception as e:
            logger.error(f"Error getting signing key: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify the Azure AD token and return the payload"""
        try:
            # Get the signing key
            signing_key = self.get_signing_key(token)
            
            # Verify and decode the token with the correct audience format
            expected_audience = f"api://{self.client_id}"
            
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=expected_audience,
                issuer=self.issuer
            )
            
            return payload
            
        except JWTError as e:
            logger.error(f"JWT verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
    
    def extract_username(self, payload: Dict[str, Any]) -> str:
        """Extract username from token payload"""
        # Azure AD typically uses 'preferred_username' or 'upn' for username
        username = payload.get('preferred_username') or payload.get('upn') or payload.get('email')
        
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username not found in token"
            )
        
        return username
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Dependency to get current authenticated user"""
        try:
            logger.info("=== AUTHENTICATION START ===")
            token = credentials.credentials
            logger.info(f"Token received: {token[:50]}...")
            logger.info("Attempting to verify token...")
            
            payload = self.verify_token(token)
            logger.info(f"Token verified successfully. Payload keys: {list(payload.keys())}")
            
            username = self.extract_username(payload)
            logger.info(f"Extracted username: {username}")
            
            user_data = {
                "username": username,
                "email": payload.get("unique_name"),
                "name": payload.get("name"),
                "roles": payload.get("roles", []),
                "sub": payload.get("sub"),  # Subject (user ID)
                "aud": payload.get("aud"),  # Audience
                "iss": payload.get("iss")   # Issuer
            }
            logger.info(f"User data: {user_data}")
            logger.info("=== AUTHENTICATION SUCCESS ===")
            return user_data
            
        except HTTPException:
            logger.error("=== AUTHENTICATION HTTP EXCEPTION ===")
            raise
        except Exception as e:
            logger.error(f"=== AUTHENTICATION ERROR ===")
            logger.error(f"Authentication error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"=== END AUTHENTICATION ERROR ===")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )

# Global instance of the auth middleware
auth_middleware = AzureAuthMiddleware()

# Dependency for protected routes
def require_auth():
    """Dependency that requires authentication"""
    return auth_middleware.get_current_user

# Decorator for protecting routes
def protected_route(func):
    """Decorator to protect routes with authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This will be handled by the dependency injection
        return await func(*args, **kwargs)
    return wrapper 