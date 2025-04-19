# Pydantic models for request/response
from pydantic import BaseModel, EmailStr

class EmailRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str
