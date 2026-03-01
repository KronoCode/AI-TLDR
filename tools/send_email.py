"""Tool: send TLDR to your email (use AWS SES in production)."""
import os
import smtplib
import mlflow
from config import EMAIL_FROM, EMAIL_TO
from email.mime.text import MIMEText

@mlflow.trace(name="mail_sender_tool")
def send_email(mail_content: str, mail_object: str = "AI TLDR – Daily digest") -> str:
    """Send the TLDR digest to the user's email. Call this last after you have the final content."""

    if not EMAIL_FROM or not EMAIL_TO or not os.getenv("EMAIL_PASSWORD_SENDER"):
        print(f"[Email not configured] To: {EMAIL_TO}\nSubject: {mail_object}\n\n{mail_content[:500]}...")
        return "Email not configured; content printed to console."

    send(EMAIL_FROM, EMAIL_TO, mail_object, mail_content)

    return "Email sent."


def send(from_email: str, to_email: str, mail_object: str, mail_content: str) -> None:
    """Send an email using SMTP."""
    msg = MIMEText(mail_content, "plain", "utf-8")
    msg["Subject"] = mail_object
    msg["From"] = from_email
    msg["To"] = to_email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        email_password = os.getenv("EMAIL_PASSWORD_SENDER")
        server.login(from_email, email_password)
        server.sendmail(from_email, to_email, msg.as_bytes())