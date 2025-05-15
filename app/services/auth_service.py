
import datetime
import os
from typing import Tuple, Optional
import jwt
import pytz
import redis 
from werkzeug.security import generate_password_hash, check_password_hash

from app.services.otp_service import generate_secret_key, generate_otp, store_otp, verify_and_validate_otp
from app.services.email_service import send_email_otp
from app.config.settings import (
    supabase,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXP_DELTA_SECONDS,
)

# Handle optional REDIS_URL
try:
    from app.config.settings import REDIS_URL as _SETTINGS_REDIS_URL  # type: ignore[attr-defined]
except ImportError:
    _SETTINGS_REDIS_URL = None

REDIS_URL: str = _SETTINGS_REDIS_URL or os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Rate limiting settings
WINDOW_SECONDS = 60
REGISTER_LIMIT = 5
LOGIN_LIMIT = 10


def _is_rate_limited(key: str, limit: int, window: int) -> bool:
    """Return True if the counter for key exceeds limit within window seconds."""
    try:
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, window)
        return current > limit
    except redis.exceptions.RedisError:
        return False  # Fail open


def create_jwt(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(pytz.UTC) + datetime.timedelta(minutes=JWT_EXP_DELTA_SECONDS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def register_user(email: str, password: str) -> Tuple[Optional[dict], Optional[str]]:
    rate_key = f"rl:register:{email.lower()}"
    if _is_rate_limited(rate_key, REGISTER_LIMIT, WINDOW_SECONDS):
        return None, "Too many registration attempts. Please try again later."

    existing = supabase.table("users").select("id").eq("email", email).execute().data
    if existing:
        return None, "User already exists"

    hashed = generate_password_hash(password)
    new_user = {
        "email": email,
        "password": hashed,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    supabase.table("users").insert(new_user).execute()
    redis_client.delete(rate_key)
    return new_user, None


def initiate_otp_auth(user_id: str, email: str) -> Tuple[Optional[bool], Optional[str]]:
    secret_key = generate_secret_key()
    otp_code = generate_otp(secret_key, length=6)

    if not store_otp(user_id, otp_code):
        return None, "Failed to store OTP"

    if not send_email_otp(email, str(otp_code)):
        return None, "Failed to send OTP email"

    return True, None


def authenticate_user(email: str, password: str) -> Tuple[Optional[str], Optional[str]]:
    rate_key = f"rl:login:{email.lower()}"
    if _is_rate_limited(rate_key, LOGIN_LIMIT, WINDOW_SECONDS):
        return None, "Too many login attempts. Please try later."

    try:
        resp = supabase.table("users").select("id,email,password_hash").eq("email", email).single().execute()
    except Exception:
        return None, "Invalid credentials"

    if not resp.data:
        return None, "Invalid credentials"

    user = resp.data
    if not check_password_hash(user["password_hash"], password):
        return None, "Invalid credentials"

    success, error = initiate_otp_auth(user["id"], user["email"])
    if not success:
        return None, error

    redis_client.delete(rate_key)

    temp_payload = {
        "user_id": user["id"],
        "email": user["email"],
        "exp": datetime.datetime.now(pytz.UTC) + datetime.timedelta(minutes=JWT_EXP_DELTA_SECONDS),
        "first_factor_complete": True
    }
    temp_token = jwt.encode(temp_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return temp_token, None


def complete_authentication(user_id: str, otp_code: str) -> Tuple[Optional[str], Optional[str]]:
    valid = verify_and_validate_otp(user_id, otp_code)
    if not valid:
        return None, "Invalid or expired OTP"
    return create_jwt(user_id), None


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
