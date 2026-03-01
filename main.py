"""
AI TLDR – runs daily at 6 AM (AWS EventBridge + Lambda).
Orchestrates: TLDR agent (finance/business by level), news agent, summarize + email tools.
"""
from orchestrator import run_daily, ORCHESTRATOR_MODEL
import mlflow
from datetime import date  

EXPERIMENT_NAME_DEBUG = "AI TLDR TEST"
EXPERIMENT_NAME_CLOUD = f"AI TLDR DAY {date.today().strftime('%d/%m/%Y')}"

def lambda_handler(event, context):
    """AWS Lambda entrypoint for scheduled invocation (e.g. 6 AM daily)."""
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment(EXPERIMENT_NAME_CLOUD)
    run_daily()
    return {"statusCode": 200, "body": "OK"}


if __name__ == "__main__":
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment(EXPERIMENT_NAME_DEBUG)
    with mlflow.start_run(run_name=f"debug {date.today()} model {ORCHESTRATOR_MODEL}"):
        run_daily("Latest Agentic AI breakthrough and new use cases")