import argparse
from flask import Flask
from rq import Queue, Worker
from redis import Redis
from sonar_agent.webhook import app
from sonar_agent.agents import process_issue

# # Local testing
# from dotenv import load_dotenv
# load_dotenv()

# Redis connection
# redis_conn = Redis(host='localhost', port=6379)
redis_conn = Redis(host='redis', port=6379, decode_responses=True)
q = Queue(connection=redis_conn)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run sonar-agent-swarm web or worker")
    parser.add_argument("command", choices=["web", "worker"], help="Run as web server or worker")
    args = parser.parse_args()

    if args.command == "web":
        app.run(host="0.0.0.0", port=5000)
    elif args.command == "worker":
        worker = Worker([q], connection=redis_conn)
        worker.work()