"""Orchestrator: coordinates search-agent calls, writes the TLDR, and sends email."""
import json
import mlflow
from groq import Groq
import config
from datetime import date
from tools.registry import GROQ_TOOLS, ORCHESTRATOR_TOOLS

ORCHESTRATOR_MODEL = "openai/gpt-oss-120b"
MAX_SEARCH_CALLS = 2

SYSTEM_PROMPT = f"""
You are the ORCHESTRATOR of the AI TLDR workflow.

Today current date is {date.today().strftime('%d/%m/%Y')}.

Your job is to coordinate the workflow:
1. Call the web search agent to get compact article findings.
2. If findings are weak, incomplete, too broad, or missing links, call the web search agent again with specific feedback.
3. Once findings are good enough, write the TLDR from those findings.
4. Shorten it if needed.
5. Send the final TLDR via email.

If the TLDR exceeds 1000 words, needs_shortening = true

Base yourself on this WORKFLOW STATE:
{{
  "web_search_agent_called": ,
  "findings_accepted": ,
  "tldr_created": ,
  "needs_shortening": ,
  "email_sent": 
}}

Strictly follow this decision order and do not deviate:
1 - If web_search_agent_called == false → call web search agent with the topic.
2 - Else if findings_accepted == false and findings are weak → call the agent again with concise feedback and previous compact findings.
3 - Else if tldr_created == false → create TLDR from the accepted findings and set this step to true.
4 - Else if needs_shortening == true → summarize the TLDR and set this step to true (optional step).
5 - Else if email_sent == false → call send_email with the TLDR and set this step to true.
6 - Else → reply: "The TLDR mail has been sent."

A TLDR mail must:
- Starting paragraph with emojis and text to welcome the reader and introduce the topic.
- Set 1 bullet point per article found on the internet.
- Have a title for each information or topic found.
- Have a link at the bottom of the bullet point redirecting to the article source website. 
- Use emojis to make the TLDR more engaging.

RULES:
- Call exactly ONE tool per response when needed.
- Never repeat completed steps.
- Never invent tools.
- Use tool results and workflow_state only.
- Never ask search_articles to return raw article bodies.
- When calling search_articles again, pass only compact previous findings and specific feedback.
- Do not explain reasoning when calling tools.
- You may call search_articles at most {MAX_SEARCH_CALLS} times. Stop searching as soon as the findings are good enough.
- Once a tool result tells you the search limit is reached, do not search again: write the TLDR from the findings you already have and send the email.
- You must either call exactly one tool OR return the final confirmation message.
"""


def _tool_by_name(name: str):
    return {f.__name__: f for f in ORCHESTRATOR_TOOLS}.get(name)

@mlflow.trace(name="tool_call")
def run_tool(name: str, arguments: dict):
    fn = _tool_by_name(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        result = fn(**{k: v for k, v in arguments.items() if k in fn.__annotations__})
        return result if result is not None else "Done."
    except Exception as e:
        return f"Error: {e}"

@mlflow.trace(name="run_status")
def run_daily(topic: str = "finance_tips"):
    client = Groq(api_key=config.GROQ_API_KEY)

    """Let the orchestrator call the search agent, write the TLDR, and send it."""
    user_goal = (
        f"""
        Create a TLDR mail on the following topic and send it to me via email : '{topic.replace('_',' ')}'.
        Today current date is {date.today().strftime('%d/%m/%Y')}.
        You can call search_articles multiple times before sending the email if you need better findings.
        """
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_goal},
    ]

    mlflow.log_param("llm_tools", ",".join(x.__name__ for x in ORCHESTRATOR_TOOLS))
    max_rounds = 7
    search_calls = 0
    for round in range(max_rounds):
        response = client.chat.completions.create(
            model=ORCHESTRATOR_MODEL,
            messages=messages,
            tools=GROQ_TOOLS,
            tool_choice="auto",
            max_tokens=4096,
            extra_body={"reasoning_effort": "medium"}
        )

        #Get the message from the response
        msg = response.choices[0].message

        #Build message to add to context
        msg_to_append = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            msg_to_append["tool_calls"] = msg.tool_calls

        #Add the message to the messages list along with the tool calls if any
        messages.append(msg_to_append)

        #Get the tool calls from the message for this iteration
        tool_calls = msg.tool_calls or []

        #Iterate over the tool calls and run the tool
        for tool in tool_calls:
            tool_name = tool.function.name
            tool_args = json.loads(tool.function.arguments)

            # Cap how many times the search agent can be called
            if tool_name == "search_articles" and search_calls >= MAX_SEARCH_CALLS:
                result = (
                    f"Search limit reached ({MAX_SEARCH_CALLS} calls). "
                    "Do NOT call search_articles again. "
                    "Use the most recent findings handoff you already received to write the "
                    "TLDR and send the mail now."
                )
            else:
                if tool_name == "search_articles":
                    search_calls += 1
                result = run_tool(tool_name, tool_args)

            if tool_name == "send_email" and "Email sent." in str(result):
                mlflow.log_metric("search_calls", search_calls)
                mlflow.log_metric("nbr_of_rounds", round)
                return True

            messages.append({
                "role": "tool",
                "tool_call_id": tool.id,
                "content": f"Used Tool: {tool_name}. Result :{str(result)}",
            })
    
    mlflow.log_metric("nbr_of_rounds", round)
    mlflow.log_param("Workflow error", "Max rounds reached.")
    return False

# # Or log the full conversation at the end as one artifact
# def log_full_conversation(messages: list):
#     mlflow.log_text(
#         json.dumps(messages, indent=2),
#         "exchanges/full_conversation.json"
#     )