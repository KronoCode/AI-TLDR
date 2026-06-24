"""Helpers for converting Python functions to Groq/OpenAI tool schemas."""

import inspect


def function_to_tool_schema(func):
    hints = func.__annotations__
    signature = inspect.signature(func)
    properties = {}
    required = []

    for param, type_ in hints.items():
        if param == "return":
            continue
        properties[param] = {
            "type": "string"
        }
        if signature.parameters[param].default is inspect.Parameter.empty:
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
