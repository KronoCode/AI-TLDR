"""Config: env vars for AWS, email, API keys. Use SSM/Secrets Manager in production."""
import os

LEVELS = ("beginner", "intermediate", "expert")
TOPIC_CHOICES = ("finance_tips", "business_concepts")

# Email (e.g. SES in AWS)
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")
# Optional: news API key, etc.
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API", "")
