#email_service.py
import smtplib
import os
from app.config.settings import EMAIL_USER, EMAIL_PASSWORD

def send_email_otp(to_email: str, otp: str):
    """Send an email with the OTP code"""
    subject = "Your OTP Code for Authentication"
    body = f"""
    Hello,
    
    Your one-time password (OTP) for authentication is: {otp}
    
    This code will expire in 5 minutes. Do not share this code with anyone.
    
    Best regards,
    Maktabeti team 
    """
    message = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, to_email, message)
        return True
    except Exception as e:
        import traceback
        print(f"Error sending email: {e}")
        traceback.print_exc()  # Print the full traceback
        return False
    

