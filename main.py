"""
AI TLDR – runs daily at 6 AM (AWS EventBridge + Lambda).
Orchestrates: TLDR agent (finance/business by level), news agent, summarize + email tools.
"""
from orchestrator import run_daily

def lambda_handler(event, context):
    """AWS Lambda entrypoint for scheduled invocation (e.g. 6 AM daily)."""
    run_daily()
    return {"statusCode": 200, "body": "OK"}


if __name__ == "__main__":
    run_daily()