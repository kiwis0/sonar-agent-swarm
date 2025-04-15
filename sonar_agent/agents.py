import logging
from sonar_agent.config import get_config
from github import Github
from anthropic import Anthropic, AnthropicError
import httpx

logger = logging.getLogger(__name__)

class FixerAgent:
    def __init__(self):
        self.client = Anthropic(api_key=get_config('ANTHROPIC_API_KEY'), http_client=httpx.Client())

    def fix(self, issue):
        prompt = f"SonarQube issue in {issue['file']} at line {issue['line']}: \"{issue['desc']}\"\nProvide a Python fix. Return only the code block."
        try:
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219x1",
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
        if not fix or "error" in fix.lower():
            logger.warning(f"Invalid fix for {issue['desc']}")
            return False
        logger.info(f"Validated fix for {issue['desc']}")
        return True

class PRAgent:
    def create_pr(self, issue, fix):
        g = Github(get_config('GITHUB_TOKEN'))
        repo = g.get_repo(get_config('REPO_NAME'))
        branch = f"fix-{issue['desc'].replace(' ', '-')[:50]}"
        try:
            main_branch = repo.get_branch("main")
            repo.create_git_ref(f"refs/heads/{branch}", main_branch.commit.sha)
            content = f"# Auto-fix for {issue['desc']}\n{fix}\n"
            repo.create_file(issue["file"], f"Fix {issue['desc']}", content, branch=branch)
            pr = repo.create_pull(
                title=f"Fix {issue['desc']}",
                body="Auto-fix by sonar-agent-swarm",
                head=branch,
                base="main"
            )
            logger.info(f"PR #{pr.number} created")
        except Exception as e:
            logger.error(f"PR failed: {e}")

def process_issue(issue):
    """Process a single SonarQube issue from the RQ queue."""
    logger.info(f"Processing issue: {issue['desc']}")
    fixer = FixerAgent()
    validator = ValidatorAgent()
    pr_agent = PRAgent()
    fix = fixer.fix(issue)
    if fix and validator.validate(issue, fix):
        pr_agent.create_pr(issue, fix)
    else:
        logger.warning(f"Skipped {issue['desc']} - fix invalid")
    logger.info(f"Finished processing: {issue['desc']}")