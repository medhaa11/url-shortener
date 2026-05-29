import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

CACHE_TTL = 3600  # 1 hour

def cache_set(short_code: str, original_url: str):
    r.setex(short_code, CACHE_TTL, original_url)

def cache_get(short_code: str) -> str | None:
    return r.get(short_code)

def cache_delete(short_code: str):
    r.delete(short_code)