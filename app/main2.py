import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_test_email(to_email, subject, body, email_user, email_password):
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.sendmail(email_user, to_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    # Replace with your actual email details
    email_user = "safa.achour@ensia.edu.dz"  # Replace this
    email_password = "safsofatebha"  # Replace this
    to_email = "safaachour0105@9gmail.com"  # Replace this
    subject = "Test Email"
    body = "This is a test email sent from Python."
    send_test_email(to_email, subject, body, email_user, email_password)