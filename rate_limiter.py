import time
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

WINDOW_SECONDS = 60
MAX_REQUESTS    = 5

def is_rate_limited(ip: str) -> bool:
    key = f"rate:{ip}"
    now = time.time()
    window_start = now - WINDOW_SECONDS

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)   # remove timestamps outside window
    pipe.zadd(key, {str(now): now})               # add current request timestamp
    pipe.zcard(key)                               # count requests in window
    pipe.expire(key, WINDOW_SECONDS)              # auto-cleanup the key
    results = pipe.execute()

    request_count = results[2]
    return request_count > MAX_REQUESTS