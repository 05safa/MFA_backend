from pydantic import BaseModel, EmailStr, Field

class Register(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class Login(BaseModel):
    email: EmailStr
    password: str

class OTPVerify(BaseModel):
    token: str  # The temporary token received after first-factor auth
    otp_code: str  # The OTP code entered by the user