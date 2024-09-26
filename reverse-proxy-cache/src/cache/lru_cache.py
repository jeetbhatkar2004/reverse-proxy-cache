import redis
import time

class LRUCache:
    def __init__(self, capacity: int, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.capacity = capacity
        self.key_access_time = f"lru_cache_access_time_{id(self)}"
        self.hits_key = f"cache_hits_{id(self)}"
        self.misses_key = f"cache_misses_{id(self)}"

    def get(self, key: str) -> str:
        value = self.redis.get(key)
        if value is None:
            # Increment misses atomically in Redis
            self.redis.incr(self.misses_key)
            return -1
        else:
            # Increment hits atomically in Redis
            self.redis.incr(self.hits_key)
            current_time = time.time()
            self.redis.zadd(self.key_access_time, {key: current_time})
            return value.decode('utf-8')

    def put(self, key: str, value: str) -> None:
        self.redis.set(key, value)
        current_time = time.time()
        self.redis.zadd(self.key_access_time, {key: current_time})

        cache_size = self.redis.zcard(self.key_access_time)
        if cache_size > self.capacity:
            # Evict the least recently used item
            oldest = self.redis.zrange(self.key_access_time, 0, 0)
            if oldest:
                oldest_key = oldest[0]
                self.redis.delete(oldest_key)
                self.redis.zrem(self.key_access_time, oldest_key)

    def contains(self, key: str) -> bool:
        return self.redis.exists(key) == 1

    def get_cache_stats(self):
        # Retrieve hits and misses from Redis
        hits = int(self.redis.get(self.hits_key) or 0)
        misses = int(self.redis.get(self.misses_key) or 0)
        return {"hits": hits, "misses": misses}

    def items(self):
        keys = self.redis.zrange(self.key_access_time, 0, -1)
        items = []
        for key in keys:
            value = self.redis.get(key)
            if value is not None:
                items.append((key.decode('utf-8'), value.decode('utf-8')))
        return items

    def clear(self):
        # Flush the entire Redis database used by this cache
        self.redis.flushdb()
        # Reset hits and misses counters in Redis
        self.redis.set(self.hits_key, 0)
        self.redis.set(self.misses_key, 0)

    def __str__(self):
        items = self.items()
        return str(dict(items))
