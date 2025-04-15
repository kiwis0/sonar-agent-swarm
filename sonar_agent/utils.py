import re
import logging
from github import GithubException

logger = logging.getLogger(__name__)

SONAR_ISSUE_PATTERN = re.compile(r'SonarQube issue in (\S+) at line (\d+): (.+)')

def parse_sonar_issue(issue_body):
    match = SONAR_ISSUE_PATTERN.search(issue_body)
    if match:
        return {
            'file': match.group(1),
            'line': int(match.group(2)),
            'desc': match.group(3)
        }
    logger.debug(f"No SonarQube issue found in: {issue_body}")
    return None

def get_file_content(repo, file_path):
    try:
        content = repo.get_contents(file_path).decoded_content.decode('utf-8')
        return content
    except GithubException as e:
        logger.error(f"Failed to fetch {file_path}: {e}")
        return None