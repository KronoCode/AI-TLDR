"""Tool: send TLDR to your email (use AWS SES in production)."""
import os
import smtplib
from config import EMAIL_FROM, EMAIL_TO


def send_tldr_email(content: str, subject: str = "AI TLDR – Daily digest") -> str:
    """Send the TLDR digest to the user's email. Call this last after you have the final content."""
    if not EMAIL_FROM or not EMAIL_TO or not os.getenv("EMAIL_PASSWORD_SENDER"):
        print(f"[Email not configured] To: {EMAIL_TO}\nSubject: {subject}\n\n{content[:500]}...")
        return "Email not configured; content printed to console."
    send_email(EMAIL_FROM, EMAIL_TO, subject, content)
    return "Email sent."


def send_email(from_email: str, to_email: str, subject: str, content: str) -> None:
    """Send an email using SMTP."""
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(from_email, os.getenv("EMAIL_PASSWORD_SENDER"))
        server.sendmail(from_email, to_email, f"Subject: {subject}\n\n{content}")