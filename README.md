# sonar-agent-swarm

A Flask-based tool to auto-fix SonarQube issues in GitHub repos using Claude.

## Features
- Listens for GitHub webhooks
- Parses SonarQube issues
- Generates fixes with Claude
- Validates fixes
- Creates PRs
- Scales with multiprocessing

## Setup
1. Clone: `git clone https://github.com/yourusername/sonar-agent-swarm.git`
2. Install: `pip install .`
3. Copy `config.ini.example` to `config.ini` and configure it
4. Run: `sonar-agent-swarm`

## Configuration
Edit `config.ini` or set env vars (e.g., `GITHUB_TOKEN`).

## Usage
Set a GitHub webhook to `http://your-server:port/webhook` with your secret. Create issues like "SonarQube issue in main.py at line 10: unused variable".

## Scalability
Uses a Queue and configurable workers to handle high demand.