"""Search agent: finds articles on the web; a separate step builds the handoff."""

import json
import mlflow
from groq import Groq

import config
from agents.handoff import (
    parse_search_handoff,
    truncate_tool_result,
    validate_and_trim_handoff,
)
from tools.browse_internet import browse_internet
from tools.schema import function_to_tool_schema

SEARCH_AGENT_MODEL = "llama-3.3-70b-versatile"
MAX_SEARCH_ROUNDS = 3
SEARCH_AGENT_TOOLS = [browse_internet]
GROQ_SEARCH_TOOLS = [function_to_tool_schema(f) for f in SEARCH_AGENT_TOOLS]

SEARCH_SYSTEM_PROMPT = """
You are the SEARCH AGENT for the AI TLDR workflow.

You research a topic by searching the web with browse_internet and gather the most
relevant, trustworthy articles. You distill what you find into short notes and report
the articles you select. Follow the user's instructions for what to do at each step.

HOW YOU SEARCH:
- Choose an appropriate search_query and tbm for browse_internet.
- Use articles from previous searches as context to refine the next query.
- Keep short notes per article; do not retain full article bodies.
- Call exactly ONE tool per response, and do not explain your reasoning when calling a tool.
"""

HANDOFF_INSTRUCTION = """
Search is complete. Using ONLY the articles found above, return the compact JSON handoff
for the orchestrator in this exact shape:
{
  "articles": [
    {"title": "...", "summary": "2-4 sentences, max 80 words", "url": "https://..."}
  ],
  "coverage_note": "optional: gaps or why you searched again"
}

RULES:
- Return 3 to 5 articles.
- Each summary must be 2-4 sentences and at most 80 words.
- Every article must include title, summary, and url sourced from the search results.
- Your response must be valid JSON only, with no markdown fences and no other text.
"""


def _truncate_browse_result(tool_name: str, result: str) -> str:
    if tool_name == "browse_internet":
        return truncate_tool_result(result)
    return result


def _run_browse_tool(arguments: dict) -> str:
    try:
        result = browse_internet(
            search_query=arguments.get("search_query", ""),
            tbm=arguments.get("tbm", ""),
        )
    except Exception as e:
        result = f"Error: {e}"
    return _truncate_browse_result("browse_internet", str(result))


def _append_assistant_message(messages: list, msg) -> None:
    msg_to_append = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        msg_to_append["tool_calls"] = msg.tool_calls
    messages.append(msg_to_append)


def _run_search_loop(client, messages: list, max_rounds: int) -> int:
    """Run web-search rounds only. Returns the number of rounds executed."""
    rounds_used = 0
    for _ in range(max_rounds):
        rounds_used += 1
        response = client.chat.completions.create(
            model=SEARCH_AGENT_MODEL,
            messages=messages,
            tools=GROQ_SEARCH_TOOLS,
            tool_choice="auto",
            max_tokens=2048,
        )

        choice = response.choices[0]
        _append_assistant_message(messages, choice.message)

        tool_calls = choice.message.tool_calls or []
        if not tool_calls:
            break

        for tool in tool_calls:
            tool_name = tool.function.name
            if tool_name != "browse_internet":
                result = f"Unknown tool: {tool_name}"
            else:
                tool_args = json.loads(tool.function.arguments)
                result = _run_browse_tool(tool_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool.id,
                "content": f"Used Tool: {tool_name}."
                           f"Result: {result}"
            })

    return rounds_used


def _build_handoff(client, messages: list) -> str | None:
    """Tool-free call that turns the gathered articles into the JSON handoff."""
    messages.append({"role": "user", "content": HANDOFF_INSTRUCTION})
    response = client.chat.completions.create(
        model=SEARCH_AGENT_MODEL,
        messages=messages,
        tool_choice="none",
        max_tokens=2048,
    )
    choice = response.choices[0]
    _append_assistant_message(messages, choice.message)
    return choice.message.content


@mlflow.trace(name="search_agent")
def run_search_agent(topic: str, feedback: str = "", previous_findings: str = "") -> dict:
    client = Groq(api_key=config.GROQ_API_KEY)
    user_goal = (
        f"Find the best articles on: '{topic.replace('_', ' ')}'."
        f"You can search the web up to {MAX_SEARCH_ROUNDS} times and choose as much as {config.MAX_ARTICLES} articles per web search."
        "Search the web and distill findings.\n"
        f"Orchestrator feedback: {feedback or 'None'}\n"
        f"Previous compact findings, if any: {previous_findings or 'None'}"
    )
    messages = [
        {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
        {"role": "user", "content": user_goal},
    ]

    mlflow.log_param("search_agent_tools", ",".join(f.__name__ for f in SEARCH_AGENT_TOOLS))

    rounds_used = _run_search_loop(client, messages, MAX_SEARCH_ROUNDS)
    mlflow.log_metric("search_rounds", rounds_used)

    final_content = _build_handoff(client, messages)

    try:
        return validate_and_trim_handoff(parse_search_handoff(final_content))
    except (ValueError, json.JSONDecodeError) as e:
        mlflow.log_param("search_agent_error", str(e))
        repair_content = _retry_json_repair(client, messages, str(e))
        if repair_content:
            try:
                return validate_and_trim_handoff(parse_search_handoff(repair_content))
            except (ValueError, json.JSONDecodeError) as retry_err:
                mlflow.log_param("search_agent_error", f"Repair failed: {retry_err}")
        return {"articles": []}


def _retry_json_repair(client, messages: list, error: str) -> str | None:
    """Re-ask for valid JSON without searching again."""
    messages.append({
        "role": "user",
        "content": (
            f"Your last response was invalid: {error}. "
            "Reply with ONLY valid JSON matching the handoff schema."
        ),
    })
    response = client.chat.completions.create(
        model=SEARCH_AGENT_MODEL,
        messages=messages,
        tool_choice="none",
        max_tokens=2048,
    )
    choice = response.choices[0]
    _append_assistant_message(messages, choice.message)
    return choice.message.content


def search_articles(topic: str, feedback: str = "", previous_findings: str = "") -> str:
    """
    Run the search agent and return compact article findings as JSON.

    Use feedback to ask for broader, narrower, more recent, or higher-quality sources.
    Pass previous_findings only as compact JSON summaries, never raw article bodies.
    """
    return json.dumps(
        run_search_agent(topic=topic, feedback=feedback, previous_findings=previous_findings),
        ensure_ascii=False,
    )
