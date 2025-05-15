from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import datetime
import pytz
from app.models.schemas import Register, Login, OTPVerify
from app.services.auth_service import (
    register_user, authenticate_user, decode_jwt, complete_authentication
)

router = APIRouter(prefix="/auth")
security = HTTPBearer()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: Register):
    token, err = register_user(payload.email.lower(), payload.password)
    if err:
        code = status.HTTP_409_CONFLICT if "registered" in err else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(code, detail=err)
    return {"message": "Registered successfully", "token": token}

@router.post("/login")
async def login(payload: Login):
    token, err = authenticate_user(payload.email.lower(), payload.password)
    print("DEBUG TOKEN:", token)
    print("DEBUG ERROR:", err)
    if err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=err)
    return {
        "message": "First factor authenticated. Please verify OTP sent to your email.",
        "temp_token": token,
        "requires_otp": True
    }

@router.post("/verify-otp")
async def verify_otp(otp_payload: OTPVerify):
    # Decode the temporary token
    temp_payload = decode_jwt(otp_payload.token)
    if not temp_payload or not temp_payload.get("first_factor_complete"):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Complete authentication with OTP
    token, err = complete_authentication(temp_payload["user_id"], otp_payload.otp_code)
    if err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=err)
    
    # Return the final authentication token that can be used for protected routes
    return {"message": "otp verification complete", "token": token}

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = decode_jwt(token)
    if not payload:
        # differentiate expired vs invalid if you like
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Make sure the token is not a temporary first-factor token
    if payload.get("first_factor_complete") and not payload.get("second_factor_complete"):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="OTP verification required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

@router.get("/me")
async def me(user=Depends(get_current_user)):
    # `user` is the decoded JWT payload
    return {"user_id": user["user_id"]}

# Fingerprint authentication route
@router.post("/register-fingerprint")
async def register_fingerprint(fingerprint: str, user=Depends(get_current_user)):
    """Register a user's fingerprint for future authentication"""
    try:
        
        supabase.table("fingerprints").insert({
            "user_id": user["user_id"],
            "fingerprint": fingerprint,
            "created_at": datetime.datetime.utcnow().isoformat()
        }).execute()
        return {"message": "Fingerprint registered successfully"}
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register fingerprint"
        )