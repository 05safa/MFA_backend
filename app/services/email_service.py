# Handles email sending logic
import smtplib
import os
from app.config.settings import EMAIL_USER, EMAIL_PASSWORD

def send_email_otp(to_email: str, otp: str):
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"
    message = f"Subject: {subject}\n\n{body}"

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, to_email, message)
