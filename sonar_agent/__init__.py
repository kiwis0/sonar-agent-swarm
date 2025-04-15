from redis import Redis
from rq import Queue

redis_conn = Redis(host='localhost', port=6379, decode_responses=True)  # 'localhost' for local testing
q = Queue(connection=redis_conn)