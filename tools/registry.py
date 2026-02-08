"""Registry of tools/agents the orchestrator LLM can call. Docstrings and types define the tool schema."""

from agents.news_agent import get_business_news
from agents.tldr_agent import get_tldr
from tools.email_sender import send_tldr_email
from tools.summarize import summarize

# Orchestrator receives these as tools; it decides when to call each.
ORCHESTRATOR_TOOLS = [get_business_news, get_tldr, summarize, send_tldr_email]
