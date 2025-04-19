# Handles OTP generation/storage/verification
from datetime import datetime, timedelta
import random

otp_store = {}

def generate_and_store_otp(email: str) -> str:
    otp = str(random.randint(100000, 999999))
    expiry = datetime.utcnow() + timedelta(minutes=5)
    otp_store[email] = {"otp": otp, "expires_at": expiry}
    return otp

def verify_otp(email: str, otp: str):
    record = otp_store.get(email)
    if not record:
        raise ValueError("No OTP found")
    if datetime.utcnow() > record["expires_at"]:
        raise ValueError("OTP expired")
    if record["otp"] != otp:
        raise ValueError("Invalid OTP")
    del otp_store[email]
