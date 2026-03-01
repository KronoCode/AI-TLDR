"""Orchestrator: an LLM that reflects on the goal and calls agents/tools by itself."""
import json

from ollama import chat, ChatResponse  # type: ignore[import-untyped]
# from mcp_server import run_mcp_server
import mlflow
from groq import Groq
import config
from datetime import date
from tools.registry import GROQ_TOOLS, ORCHESTRATOR_TOOLS

ORCHESTRATOR_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
You are the ORCHESTRATOR of the AI TLDR workflow.

Your job is only to decide which tool to call to get the information, create the tldr, shorten it if needed and send me the content via mail.
If the TLDR exceeds 500 words, needs_shortening = true

Base yourself on this WORKFLOW STATE:
{
  "internet_searched": ,
  "tldr_created": ,
  "needs_shortening": ,
  "email_sent": 
}

Strictly follow this decision order and do not deviate:
- If internet_searched == false → scrape the internet for information on the topic given and set it to true.
- Else if tldr_created == false → create TLDR from the scraped information and set this step to true
- Else if needs_shortening == true → summarize the TLDR and set this step to true (optional step)
- Else if email_sent == false → send email with the TLDR and set this step to true
- Else → reply: "The TLDR mail has been sent."

A TLDR mail must:
- Starting paragraph with emojis and text to welcome the reader and introduce the topic.
- Have a title for each information or topic found.
- Have 3 to 5 numbered items on the information found on the topic, each one explained with a max 5 sentence paragraph
- Have a link at the bottom of the bullet point redirecting to the article source website. 

You can use the same format as the TLDR Example below:  
<start>
## 🗞️ TLDR - Tech & AI Daily | February 28, 2026

**1. OpenAI launches GPT-5**
OpenAI released its latest model claiming 50% better reasoning than GPT-4. Early benchmarks show strong performance on coding tasks.
🔗 https://example.com/openai-gpt5

**2. EU passes new AI regulation**
The European Union voted to enforce mandatory transparency rules for AI systems used in hiring and healthcare starting 2027.
🔗 https://example.com/eu-ai-law

**3. Apple acquires AI startup**
Apple quietly acquired a computer vision startup for $200M, signaling a push toward on-device AI features in iOS 20.
🔗 https://example.com/apple-acquisition

---
📬 You're receiving this because you subscribed to the TLDR digest.
<end>

RULES:
- Call exactly ONE tool per response when needed.
- Never repeat completed steps.
- Never invent tools.
- Use tool results and workflow_state only.
- Do not explain reasoning when calling tools.
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

    """Let the orchestrator LLM decide and call agents/tools to produce and send the daily TLDR."""
    user_goal = (
        f"""
        Create a TLDR mail on the following topic and send it to me via email : '{topic.replace('_',' ')}'.
        Today current date is {date.today().strftime('%d/%m/%Y')}.
        """
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_goal},
    ]

    mlflow.log_param("llm_tools", ",".join(x.__name__ for x in ORCHESTRATOR_TOOLS))
    max_rounds = 7
    for round in range(max_rounds):

        # try:
        # Call the model
        response = client.chat.completions.create(
            model=ORCHESTRATOR_MODEL,
            messages=messages,
            tools=GROQ_TOOLS,
            tool_choice="auto",
            max_tokens=2048,
            extra_body={"reasoning_effort": "medium"}
        )

        #Get the message from the response
        msg = response.choices[0].message

        #Build message to add to context
        msg_to_append = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            msg_to_append["tool_calls"] = msg.tool_calls

        # except Exception as e:
        #     msg_to_append = {"role": "user", "content": f"Resolve this error and advance in your tasks. Error: {e}"}

        #Add the message to the messages list along with the tool calls if any
        messages.append(msg_to_append)

        #Get the tool calls from the message for this iteration
        tool_calls = msg.tool_calls or []

        #Iterate over the tool calls and run the tool
        for tool in tool_calls:
            tool_name = tool.function.name
            tool_args = json.loads(tool.function.arguments)
            
            result = run_tool(tool_name, tool_args)

            # If the email tool was called and reported success, flag it
            if tool_name == "send_email" and "Email sent." in str(result):
                mlflow.log_metric("nbr_of_rounds", round)
                # log_full_conversation(messages)
                return True

            # Ollama expects tool response format
            messages.append({
                "role": "tool",
                "tool_call_id": tool.id,
                "content": f"Used Tool: {tool_name}. Result :{str(result)}",
            })
    
    mlflow.log_metric("nbr_of_rounds", round)
    mlflow.log_param("Workflow error", "Max rounds reached.")
    return False

# Or log the full conversation at the end as one artifact
def log_full_conversation(messages: list):
    mlflow.log_text(
        json.dumps(messages, indent=2),
        "exchanges/full_conversation.json"
    )