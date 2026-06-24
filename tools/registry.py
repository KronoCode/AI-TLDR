"""Tool registries scoped by the LLM actor that can call them."""

from agents.search_agent import search_articles
from tools.browse_internet import browse_internet
from tools.schema import function_to_tool_schema
from tools.send_email import send_email

SEARCH_AGENT_TOOLS = [browse_internet]
AGENT_TOOLS = [search_articles]
API_TOOLS = [send_email]
ORCHESTRATOR_TOOLS = AGENT_TOOLS + API_TOOLS


GROQ_SEARCH_TOOLS = [function_to_tool_schema(f) for f in SEARCH_AGENT_TOOLS]
GROQ_ORCHESTRATOR_TOOLS = [function_to_tool_schema(f) for f in ORCHESTRATOR_TOOLS]

# Backward-compatible alias
GROQ_TOOLS = GROQ_ORCHESTRATOR_TOOLS
