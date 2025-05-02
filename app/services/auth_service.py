import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from app.config.settings import supabase, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXP_DELTA_SECONDS

def create_jwt(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def register_user(email: str, password: str):
    # 1) Check if user already exists
    try:
        existing = supabase.table("users").select("id").eq("email", email).execute()
    except APIError:
        return None, "Failed to register"
    if existing.data:
        return None, "Email already registered"

    # 2) Hash the password
    pw_hash = generate_password_hash(password)

    # 3) Insert new user
    try:
        resp = supabase.table("users").insert({
            "email": email,
            "password_hash": pw_hash,
            "created_at": datetime.datetime.utcnow().isoformat()
        }).execute()
    except APIError:
        return None, "Failed to register"

    if not resp.data:
        return None, "Failed to register"

    user_id = resp.data[0]["id"]
    return create_jwt(user_id), None

def authenticate_user(email: str, password: str):
    try:
        resp = supabase.table("users").select("id,password_hash").eq("email", email).single().execute()
    except APIError:
        return None, "Invalid credentials"

    if not resp.data:
        return None, "Invalid credentials"

    user = resp.data
    if not check_password_hash(user["password_hash"], password):
        return None, "Invalid credentials"

    return create_jwt(user["id"]), None

def decode_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
