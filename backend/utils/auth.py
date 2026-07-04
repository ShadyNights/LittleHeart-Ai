import os
import jwt
import time
from jwt import PyJWKClient
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional, List
from backend.config import settings

class Auth:
    security = HTTPBearer()
    jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json" if settings.SUPABASE_URL else None
    
    _jwks_client: Optional[PyJWKClient] = None

    @classmethod
    def get_jwks_client(cls) -> Optional[PyJWKClient]:
        if cls._jwks_client is None and cls.jwks_url:
            cls._jwks_client = PyJWKClient(cls.jwks_url)
        return cls._jwks_client

    @staticmethod
    def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
        token = credentials.credentials
        try:
            unverified_header = jwt.get_unverified_header(token)
            
            # If the token has a Key ID, it's asymmetric (RS256/ES256) - fetch from JWKS
            if "kid" in unverified_header:
                jwks_client = Auth.get_jwks_client()
                if not jwks_client:
                    raise HTTPException(status_code=500, detail="JWKS Client not initialized.")
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                key_to_use = signing_key.key
            else:
                # No Key ID means it's symmetric (HS256) - use the JWT secret directly
                key_to_use = settings.SUPABASE_JWT_SECRET
                if not key_to_use:
                    raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET not configured.")

            payload = jwt.decode(
                token, 
                key_to_use,
                algorithms=["HS256", "RS256", "ES256"], 
                audience="authenticated",
                options={
                    "verify_exp": True, 
                    "verify_nbf": True,
                    "verify_iss": False,
                    "verify_aud": True
                }
            )
            
            if "sub" not in payload:
                raise HTTPException(status_code=401, detail="Token missing subject claim.")
                
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired.")
        except jwt.InvalidAudienceError:
            raise HTTPException(status_code=401, detail="Invalid token audience.")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Identity verification failed: {str(e)}")

async def get_user_id(user: Dict[str, Any] = Depends(Auth.get_current_user)) -> str:
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token.")
    return str(user_id)

async def get_raw_token(credentials: HTTPAuthorizationCredentials = Security(Auth.security)) -> str:
    return credentials.credentials

def require_role(allowed_roles: List[str]):
    async def role_checker(user: Dict[str, Any] = Depends(Auth.get_current_user)):
        from backend.services.supabase_service import SupabaseService
        supabase = SupabaseService()
        user_id = user.get("sub")
        
        profile = supabase.client.table("user_profiles").select("role").eq("id", user_id).single().execute()
        if not profile.data:
            raise HTTPException(status_code=403, detail="User profile not found. Access denied.")
        
        user_role = profile.data.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Insufficient permissions. Required: {allowed_roles}")
        
        return user
    return role_checker
