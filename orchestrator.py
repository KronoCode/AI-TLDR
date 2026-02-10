"""Orchestrator: an LLM that reflects on the goal and calls agents/tools by itself."""
import json

from ollama import chat, ChatResponse  # type: ignore[import-untyped]

from tools.registry import ORCHESTRATOR_TOOLS

ORCHESTRATOR_MODEL = "llama3.2"

SYSTEM_PROMPT = """You are the orchestrator for the AI TLDR pipeline. Your job is to achieve the user's goal by calling the right tools in the right order.

Available tools:
- get_business_news(): fetch latest world business news. Call first if the user wants news-informed content.
- get_tldr(level, topic, news_context): create a TLDR. level is one of: beginner, intermediate, expert. topic is finance_tips or business_concepts. Pass news_context from get_business_news if you have it.
- summarize(text, max_sentences): shorten long text; use before emailing if the TLDR is very long.
- send_tldr_email(content, subject): send the final digest to the user's email. Call last with the content to send.

Reflect on what the user asked for, then call the tools you need. You can call multiple tools; use tool results to decide the next step. When you have the final digest ready, call send_tldr_email with that content. After that, reply briefly to the user that the digest was sent."""


def _tool_by_name(name: str):
    return {f.__name__: f for f in ORCHESTRATOR_TOOLS}.get(name)


def run_tool(name: str, arguments: dict):
    fn = _tool_by_name(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        result = fn(**{k: v for k, v in arguments.items() if k in fn.__annotations__})
        return result if result is not None else "Done."
    except Exception as e:
        return f"Error: {e}"


def run_daily(level: str = "intermediate", topic: str = "finance_tips"):
    """Let the orchestrator LLM decide and call agents/tools to produce and send the daily TLDR."""
    user_goal = (
        f"Run the daily AI TLDR: create a digest for level '{level}' about '{topic.replace('_', ' ')}', "
        "optionally use latest business news, then send it to my email."
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_goal},
    ]
    max_rounds = 15
    for _ in range(max_rounds):
        response = chat(
            model=ORCHESTRATOR_MODEL,
            messages=messages,
            tools=ORCHESTRATOR_TOOLS,
        )
        #Get the message from the response
        msg = response.get("message", {});
        #Add the message to the messages list along with the tool calls if any
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": msg.get("tool_calls")})

        #Get the tool calls from the message for this iteration
        tool_calls = msg.get("tool_calls") or []
        #If there are no tool calls that means the result is ready, return the content of the message
        if not tool_calls:
            return msg.get("content", "")

        #Iterate over the tool calls and run the tool
        for tool in tool_calls:
            fn = tool.get("function") or tool.get("name")

            if isinstance(fn, dict):
                name = fn.get("name")
                raw_args = fn.get("arguments", "{}")
            else:
                name = fn
                raw_args = tool.get("arguments", "{}")
            args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            result = run_tool(name, args)
            # Ollama expects tool response format
            messages.append({
                "role": "tool",
                "content": str(result),
                "name": name,
            })

    return "Max rounds reached."
