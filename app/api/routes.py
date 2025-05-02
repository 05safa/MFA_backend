from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.schemas import Register, Login
from app.services.auth_service import register_user, authenticate_user, decode_jwt

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
    if err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=err)
    return {"message": "Logged in successfully", "token": token}

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = decode_jwt(token)
    print("Payload:", payload)
    if not payload:
        # differentiate expired vs invalid if you like
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

@router.get("/me")
async def me(user=Depends(get_current_user)):
    # `user` is the decoded JWT payload
    return {"user_id": user["user_id"]}