"""Registry of tools/agents the orchestrator LLM can call. Docstrings and types define the tool schema."""

from tools.browse_internet import browse_internet
from tools.send_email import send_email

# Orchestrator receives these as tools; it decides when to call each.
ORCHESTRATOR_TOOLS = [browse_internet, send_email]


def function_to_tool_schema(func):
    hints = func.__annotations__
    properties = {}
    required = []
    
    for param, type_ in hints.items():
        if param == "return":
            continue
        properties[param] = {
            "type": "string"  # extend this if you have int/bool params
        }
        required.append(param)
    
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }

# Convert your list automatically
GROQ_TOOLS = [function_to_tool_schema(f) for f in ORCHESTRATOR_TOOLS]