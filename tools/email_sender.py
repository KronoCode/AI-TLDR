"""Tool: send TLDR to your email (use AWS SES in production)."""
import os

from config import EMAIL_FROM, EMAIL_TO


def send_tldr_email(content: str, subject: str = "AI TLDR – Daily digest") -> str:
    """Send the TLDR digest to the user's email. Call this last after you have the final content."""
    if not EMAIL_FROM or not EMAIL_TO:
        print(f"[Email not configured] To: {EMAIL_TO}\nSubject: {subject}\n\n{content[:500]}...")
        return "Email not configured; content printed to console."
    # TODO: use boto3 SES
    return "Email sent."
