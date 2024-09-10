import redis
import random

class RRCache:
    def __init__(self, capacity: int, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
        self.key_set = 'rr_keys'

    def get(self, key: str) -> str:
        if not self.redis.exists(key):
            self.misses += 1
            return -1
        self.hits += 1
        return self.redis.get(key)

    def put(self, key: str, value: str) -> None:
        if not self.redis.exists(key):
            self.misses += 1
            if self.redis.scard(self.key_set) >= self.capacity:
                random_key = self.redis.srandmember(self.key_set)
                self.redis.srem(self.key_set, random_key)
                self.redis.delete(random_key)
        else:
            self.hits += 1
        self.redis.set(key, value)
        self.redis.sadd(self.key_set, key)

    def contains(self, key: str) -> bool:
        return self.redis.exists(key)

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return str(self.redis.smembers(self.key_set))