from fastapi import APIRouter
from app.models.schemas import EmailRequest, OTPVerify
from app.services.otp_service import generate_and_store_otp, verify_otp
from app.services.email_service import send_email_otp

router = APIRouter()

@router.post("/send-otp")
def send_otp(req: EmailRequest):
    otp = generate_and_store_otp(req.email)
    send_email_otp(req.email, otp)
    return {"message": "OTP sent"}

@router.post("/verify-otp")
def verify_otp_route(data: OTPVerify):
    verify_otp(data.email, data.otp)
    return {"message": "OTP verified"}
