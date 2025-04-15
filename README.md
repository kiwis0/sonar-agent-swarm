# sonar-agent-swarm

this tool that auto-fixes sonarqube issues in github repos. it listens for webhooks, uses claude to spit out fixes, and makes them into PRs. think autonomous agents, scalable queues, and clean execution. this is the start of something that can be simply added to someones project. 

## what it does
- catches github issue webhooks for sonarqube stuff
- parses issues like "SonarQube issue in main.py at line 10: unused var"
- claude (anthropic api) generates a fix
- validates it, then makes a PR
- runs in docker with redis for queueing jobs

## setup
1. clone this: `git clone https://github.com/kiwis0/sonar-agent-swarm.git`
2. copy `.env.example` to `.env`, toss in your github token, webhook secret, repo name, anthropic key
3. run `docker-compose up -d`
4. fire up ngrok: `ngrok http 500` for local testing 