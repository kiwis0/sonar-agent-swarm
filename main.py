import os
import hmac
import hashlib
import logging
import platform
from dotenv import load_dotenv
from flask import Flask, request, abort
from github import Github
from multiprocessing import Process, Queue
from anthropic import Anthropic, AnthropicError
import httpx  # Explicit import

# Cross-platform logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
REPO_NAME = os.getenv("REPO_NAME")
PORT = int(os.getenv("PORT", 5000))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not all([GITHUB_TOKEN, WEBHOOK_SECRET, REPO_NAME, ANTHROPIC_API_KEY]):
    logger.error("Missing env vars")
    exit(1)

app = Flask(__name__)
issue_queue = Queue()
anthropic_client = Anthropic(
    api_key=ANTHROPIC_API_KEY,
    http_client=httpx.Client()  # Force clean httpx client, no proxies
)

# Scanner Agent: Catch SonarQube issues
def parse_sonar_issue(issue_body):
    if "SonarQube" in issue_body:
        try:
            desc = issue_body.split(": ")[1].strip()
            return {"file": "main.py", "line": 1, "desc": desc}
        except IndexError:
            return None
    return None

class FixerAgent:
    def fix(self, issue):
        try:
            # Prompt Claude 
            prompt = f"""SonarQube issue in {issue['file']} at line {issue['line']}:
            "{issue['desc']}"
            Provide a Python fix. Return only the code block."""
            response = anthropic_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            fix = response.content[0].text.strip()
            logger.info(f"Claude fixed: {issue['desc']}")
            return fix
        except AnthropicError as e:
            logger.error(f"Anthropic error: {e}")
            return None

class ValidatorAgent:
    def validate(self, issue, fix):
        # Mock validation (Chris wants this)
        if not fix or "error" in fix.lower():
            logger.warning(f"Invalid fix for {issue['desc']}")
            return False
        # Could add Claude check here later
        logger.info(f"Validated fix for {issue['desc']}")
        return True

class PRAgent:
    def __init__(self):
        self.g = Github(GITHUB_TOKEN)
        self.repo = self.g.get_repo(REPO_NAME)

    def create_pr(self, issue, fix):
        branch = f"fix-{issue['desc'].replace(' ', '-')[:50]}"
        try:
            main_branch = self.repo.get_branch("main")
            self.repo.create_git_ref(f"refs/heads/{branch}", main_branch.commit.sha)
            content = f"# Auto-fix for {issue['desc']}\n{fix}\n"
            self.repo.create_file(issue["file"], f"Fix {issue['desc']}", content, branch=branch)
            pr = self.repo.create_pull(
                title=f"Fix {issue['desc']}",
                body="Auto-fix by sonar-agent-swarm via Claude",
                head=branch,
                base="main"
            )
            logger.info(f"PR #{pr.number} created")
        except Exception as e:
            logger.error(f"PR failed: {e}")

# Supervisor: Process issues like Chris’s setup
def process_issues(queue):
    fixer = FixerAgent()
    validator = ValidatorAgent()
    pr_agent = PRAgent()
    while True:
        issue = queue.get()
        if issue is None:
            break
        fix = fixer.fix(issue)
        if fix and validator.validate(issue, fix):
            pr_agent.create_pr(issue, fix)
        else:
            logger.warning(f"Skipped {issue['desc']} - fix invalid")
        queue.task_done()

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    logger.info("Webhook received")
    raw_data = request.get_data()  # Get raw bytes explicitly
    logger.info(f"Raw payload: {raw_data}")
    logger.info(f"Secret used: {WEBHOOK_SECRET}")
    signature = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), raw_data, hashlib.sha256).hexdigest()
    logger.info(f"Expected signature: {signature}")
    logger.info(f"Received signature: {request.headers.get('X-Hub-Signature-256')}")
    if request.headers.get("X-Hub-Signature-256") != signature:
        logger.warning("Invalid webhook signature")
        abort(403)
    payload = request.get_json()
    if payload.get("action") in ["opened", "edited"]:
        issue_body = payload["issue"]["body"]
        issue = parse_sonar_issue(issue_body)
        if issue:
            logger.info(f"Queueing: {issue['desc']}")
            issue_queue.put(issue)
            return {"status": "Issue queued"}, 200
    return {"status": "No action"}, 200

if __name__ == "__main__":
    logger.info(f"Running on {platform.system()}")
    num_workers = 3  # Scalable workers
    workers = [Process(target=process_issues, args=(issue_queue,)) for _ in range(num_workers)]
    for w in workers:
        w.start()

    logger.info(f"Server on port {PORT}")
    app.run(host="0.0.0.0", port=PORT)

    for _ in range(num_workers):
        issue_queue.put(None)
    for w in workers:
        w.join()