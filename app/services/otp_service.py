import hashlib
import secrets
from app.config.settings import supabase
import datetime

# Function to generate a random secret key
def generate_secret_key():
    return secrets.token_hex(16)  # 16 bytes (32 hex characters)
 
# Function to generate a One Time Password (OTP) using the secret key
def generate_otp(secret_key, length=6):
    # Defining the characters allowed in the OTP
    allowed_characters = "0123456789"
 
    # Generating a random OTP using the secret key and allowed characters
    otp = ''.join(secrets.choice(allowed_characters) for _ in range(length))
     
    return otp


def store_otp(user_id, otp_code):
    """Store the OTP code in the database"""
    try:
    # Calculate expiration time (5 minutes from now)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        
        # Insert new OTP record
        supabase.table("otp").insert({
            "user_id": user_id,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "otp_code": hashlib.sha512(otp_code.encode()).hexdigest(),
            "is_verified": False
        }).execute()

        return True
    except Exception as e:
        print(f"Error storing OTP: {e}")
        return False

def verify_and_validate_otp(user_id, otp_code):
    """Verify the OTP code provided by the user"""
    try:
        # Get the latest non-verified OTP for the user
        result = supabase.table("otp") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("is_verified", False) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        if not result.data:
            return False
        
        otp_record = result.data[0]
        print(otp_record)
        # Check if OTP has expired
        expires_at = datetime.datetime.fromisoformat(otp_record["expires_at"])
        if datetime.datetime.now(pytz.UTC) > expires_at:
            return False
        print(otp_record)

        # Hash the user-provided OTP and compare with stored hash
        hashed_otp = hashlib.sha512(str(otp_code).encode()).hexdigest()
        pritn(otp_record)
        print(hashed_otp)
        if hashed_otp != otp_record["otp_code"]:
            return False
        print(otp_record)

        # Mark OTP as verified
        supabase.table("otp") \
            .update({"is_verified": True}) \
            .eq("otp_id", otp_record["otp_id"]) \
            .execute()
        
        return True
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        return False