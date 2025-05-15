import datetime
import jwt
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.otp_service import generate_secret_key , generate_otp, store_otp, verify_and_validate_otp
# from supabase import Client, APIError
from app.config.settings import supabase, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXP_DELTA_SECONDS
from app.services.email_service import send_email_otp
def create_jwt(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(pytz.UTC) + datetime.timedelta(minutes=JWT_EXP_DELTA_SECONDS)
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

# Add a new function to initiate OTP authentication
def initiate_otp_auth(user_id, email):
    """Initiate OTP authentication by generating and sending an OTP"""
    # Generate a new OTP code
    secret_key = generate_secret_key()
    otp_code = generate_otp(secret_key , length=6)
    
    # Store the OTP for the user
    
    if not store_otp(user_id, otp_code):
        return None, "Failed to store OTP"
    
    # Send the OTP via email
    if not send_email_otp(email, str(otp_code)):
        return None,False
    
    return True, None

def authenticate_user(email: str, password: str):
    try:
        resp = supabase.table("users").select("id,email,password_hash").eq("email", email).single().execute()
    except Exception:
        return None, "Invalid credentials"
    
    if not resp.data:
        return None, "Invalid credentials"
    
    user = resp.data
    if not check_password_hash(user["password_hash"], password):
        return None, "Invalid credentials"
 
    # First factor is authenticated, now initiate the second factor
    success, error = initiate_otp_auth(user["id"], user["email"])
    if not success:
        return None, error
    
    # Return a temporary token containing just the user_id (not fully authenticated)
    # We'll create a special temporary token to indicate first-factor success
    temp_payload = {
        "user_id": user["id"],
        "email": user["email"],
        "exp": datetime.datetime.now(pytz.UTC) + datetime.timedelta(minutes=JWT_EXP_DELTA_SECONDS) ,
        "first_factor_complete": True
    }
    temp_token = jwt.encode(temp_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    print("DEBUG TOKEN:", temp_token)
    return temp_token, None


def complete_authentication(user_id, otp_code):
    """Complete the authentication process with OTP verification"""
    valid = verify_and_validate_otp(user_id, otp_code)
    if not valid:
        return None, "Invalid or expired OTP"
    
    # Generate a full access token
    return create_jwt(user_id), None



def decode_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
