"""
AI TLDR – runs daily at 6 AM (AWS EventBridge + Lambda).
Pipeline: search agent (web search + article compression) → orchestrator (TLDR + email).
"""
import os
import mlflow
from orchestrator import run_daily, ORCHESTRATOR_MODEL
from datetime import date
from pathlib import Path

EXPERIMENT_NAME_DEBUG = "AI TLDR TEST"
EXPERIMENT_NAME_CLOUD = f"AI TLDR DAY {date.today().strftime('%d/%m/%Y')}"
IS_DEBUG = os.getenv("IS_DEBUG", "False")
TOPIC_FILE_PATH = Path("./topic.txt") if IS_DEBUG else Path("/home/pi/newsletter/topic.txt")
DEFAULT_TOPIC = "latest ai gen research or breakthrough"

def load_topic() -> str:
    if TOPIC_FILE_PATH.is_file():
        text = TOPIC_FILE_PATH.read_text(encoding="utf-8").strip()
        if text:
            return text
    return DEFAULT_TOPIC

def lambda_handler(event, context):
    """AWS Lambda entrypoint for scheduled invocation (e.g. 6 AM daily)."""
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment(EXPERIMENT_NAME_CLOUD)
    run_daily(load_topic())
    return {"statusCode": 200, "body": "OK"}


if __name__ == "__main__":
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment(EXPERIMENT_NAME_DEBUG)
    with mlflow.start_run(run_name=f"DEBUG {date.today()} model {ORCHESTRATOR_MODEL}"):
        run_daily(load_topic())
