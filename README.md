# AI TLDR

Daily AI digest: finance/business TLDR (beginner | intermediate | expert) + world business news, summarized and emailed. Runs **once per day at 6 AM** on AWS.

## Layout

- **`main.py`** – Entrypoint; `lambda_handler` for AWS Lambda.
- **`orchestrator.py`** – Runs: news agent → TLDR agent → summarize → email.
- **`agents/`** – `tldr_agent` (finance tips or business concepts by level), `news_agent` (latest business news).
- **`tools/`** – `summarize`, `email_sender` (SES for production).

## AWS: daily 6 AM

1. **Lambda**: Package this code (or use a layer for dependencies); set handler to `main.lambda_handler`.
2. **EventBridge**: Create a rule with schedule `cron(0 6 * * ? *)` (6 AM UTC); set target to the Lambda.
3. **Env**: Set `EMAIL_FROM`, `EMAIL_TO` (and `NEWS_API_KEY` if using a news API). Prefer Secrets Manager / SSM for secrets.

## Local

```bash
pip install -r requirements.txt
# Optional: run Ollama locally with e.g. llama3.1:8b
python main.py
```

## Config

- `LEVELS`: beginner, intermediate, expert.
- `TOPIC_CHOICES`: finance_tips, business_concepts.
- Override in `run_daily(level="expert", topic="business_concepts")` or via Lambda event.
