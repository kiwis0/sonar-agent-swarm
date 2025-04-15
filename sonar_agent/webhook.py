from flask import Flask, request, abort
import hmac
import hashlib
import logging
from sonar_agent.utils import parse_sonar_issue
from sonar_agent import q
from sonar_agent.config import get_config  # Add this import

logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    logger.info("Webhook received")
    raw_data = request.get_data()
    secret = get_config('WEBHOOK_SECRET', 'default_secret')  # Fallback for testing
    signature = "sha256=" + hmac.new(secret.encode(), raw_data, hashlib.sha256).hexdigest()
    logger.debug(f"Expected signature: {signature}")
    logger.debug(f"Received signature: {request.headers.get('X-Hub-Signature-256')}")
    if request.headers.get("X-Hub-Signature-256") != signature:
        logger.warning("Invalid signature")
        abort(403)
    payload = request.get_json()
    if payload.get("action") in ["opened", "edited"]:
        issue_body = payload["issue"]["body"]
        issue = parse_sonar_issue(issue_body)
        if issue:
            logger.info(f"Queueing: {issue['desc']}")
            q.enqueue('sonar_agent.agents.process_issue', issue)
            return {"status": "Issue queued"}, 200
    return {"status": "No action"}, 200