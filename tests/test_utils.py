from sonar_agent.utils import parse_sonar_issue

def test_parse_sonar_issue():
    issue_body = "SonarQube issue in main.py at line 10: unused variable"
    issue = parse_sonar_issue(issue_body)
    assert issue == {'file': 'main.py', 'line': 10, 'desc': 'unused variable'}