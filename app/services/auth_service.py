"""Auth service with Redis‑backed rate‑limiting that is resilient when REDIS_URL is missing in settings.py.

If you already added a REDIS_URL constant to *app/config/settings.py* you can keep it; otherwise the code
falls back to the REDIS_URL environment variable (or finally to localhost). No other change is required.
"""

import datetime
import os
from typing import Tuple, Optional

import jwt
import redis
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------------------------------------------------
# Settings & configuration
# ---------------------------------------------------------------------------
# We import everything that certainly exists in your project first …
from app.config.settings import (
    supabase,  # Supabase client you already configured
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXP_DELTA_SECONDS,
)

# … then deal gracefully with the optional REDIS_URL constant.  
#   1. If REDIS_URL *is* defined in settings.py → we use it.  
#   2. Else we check an environment variable called REDIS_URL.  
#   3. Else we default to a local Redis instance.
try:
    from app.config.settings import REDIS_URL as _SETTINGS_REDIS_URL  # type: ignore[attr-defined]
except ImportError:  # settings.py simply does not export REDIS_URL
    _SETTINGS_REDIS_URL = None

REDIS_URL: str = (
    _SETTINGS_REDIS_URL
    or os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# ---------------------------------------------------------------------------
# Rate‑limiting primitives
# ---------------------------------------------------------------------------
WINDOW_SECONDS = 60  # rolling window size
REGISTER_LIMIT = 5   # max attempted registrations / window / e‑mail address
LOGIN_LIMIT = 10     # max attempted logins        / window / e‑mail address


def _is_rate_limited(key: str, limit: int, window: int) -> bool:
    """Return *True* if the counter for *key* exceeds *limit* within *window* seconds.

    Uses atomic INCR + EXPIRE so it is safe under concurrency.  
    If Redis is unavailable we *fail open* (no rate‑limit) to avoid blocking.
    """
    try:
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, window)
        return current > limit
    except redis.exceptions.RedisError:
        return False  # fail open if Redis is down


# ---------------------------------------------------------------------------
# Public API functions (register / authenticate / JWT helpers)
# ---------------------------------------------------------------------------

def register_user(email: str, password: str) -> Tuple[Optional[dict], Optional[str]]:
    """Create a new user. Returns (user_dict, error_msg)."""
    rate_key = f"rl:register:{email.lower()}"
    if _is_rate_limited(rate_key, REGISTER_LIMIT, WINDOW_SECONDS):
        return None, "Too many registration attempts. Please try again later."

    # check if user exists already
    existing = supabase.table("users").select("id").eq("email", email).execute().data
    if existing:
        return None, "User already exists"

    hashed = generate_password_hash(password)
    new_user = {"email": email, "password": hashed, "created_at": datetime.datetime.utcnow().isoformat()}
    supabase.table("users").insert(new_user).execute()

    # On success we *reset* the counter so the user can retry quickly if they made typos
    redis_client.delete(rate_key)
    return new_user, None


def authenticate_user(email: str, password: str) -> Tuple[Optional[str], Optional[str]]:
    """Validate credentials and return (jwt, error_msg)."""
    rate_key = f"rl:login:{email.lower()}"
    if _is_rate_limited(rate_key, LOGIN_LIMIT, WINDOW_SECONDS):
        return None, "Too many login attempts. Please try later."

    resp = supabase.table("users").select("id,password_hash").eq("email", email).single().execute()
    if not resp.data:
        return None, "User not found"

    user = resp.data
    if not check_password_hash(user["password_hash"], password):
        return None, "Invalid credentials"

    # Successful login → reset counter
    redis_client.delete(rate_key)

    payload = {
        "sub": email,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, None


def decode_jwt(token: str) -> dict:
    """Decode a JWT and raise jwt exceptions if invalid/expired."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
