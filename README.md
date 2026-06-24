# AI TLDR

Daily AI digest on a configurable topic, summarized and emailed. Runs **once per day at 6 AM** on AWS.

## Layout

- **`main.py`** – Entrypoint; `lambda_handler` for AWS Lambda.
- **`orchestrator.py`** – Phase 2: writes the TLDR from search results and sends email.
- **`agents/search_agent.py`** – Phase 1: searches the web, compresses articles into a JSON handoff.
- **`agents/loop.py`** – Shared Groq tool-calling loop.
- **`agents/handoff.py`** – Handoff validation and context guardrails.
- **`tools/`** – `browse_internet` (SerpAPI + scoring), `send_email` (SMTP).

## Pipeline

```
topic → search agent (browse_internet) → JSON handoff → orchestrator (TLDR + send_email)
```

## AWS: daily 6 AM

1. **Lambda**: Package this code (or use a layer for dependencies); set handler to `main.lambda_handler`.
2. **EventBridge**: Create a rule with schedule `cron(0 6 * * ? *)` (6 AM UTC); set target to the Lambda.
3. **Env**: Set `GROQ`, `NEWS_API_KEY`, `EMAIL_FROM`, `EMAIL_TO`, `EMAIL_PASSWORD_SENDER`. Prefer Secrets Manager / SSM for secrets.

## Local

```bash
pip install -r requirements.txt
export IS_DEBUG=True
python main.py
```

Set the topic in `topic.txt` (debug) or `/home/pi/newsletter/topic.txt` (production).

## Config

- `GROQ` – Groq API key.
- `NEWS_API_KEY` – SerpAPI key for web search.
- Email env vars for SMTP delivery.
