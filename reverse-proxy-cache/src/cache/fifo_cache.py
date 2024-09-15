import redis
class FIFOCache:
    def __init__(self, capacity: int, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.capacity = capacity
        self.hits_key = f"cache_hits_{id(self)}"
        self.misses_key = f"cache_misses_{id(self)}"
        self.key_list = f"fifo_keys_{id(self)}"

    # ... rest of the class remains the same ...


    def get(self, key: str) -> str:
        if not self.redis.exists(key):
            self.redis.incr(self.misses_key)
            return -1
        self.redis.incr(self.hits_key)
        value = self.redis.get(key)
        return value.decode('utf-8') if value else -1

    def put(self, key: str, value: str) -> None:
        if not self.redis.exists(key):
            self.redis.incr(self.misses_key)
            if self.redis.llen(self.key_list) >= self.capacity:
                oldest_key = self.redis.lpop(self.key_list)
                self.redis.delete(oldest_key)
        else:
            self.redis.incr(self.hits_key)
            # Remove the key from its current position in the list
            self.redis.lrem(self.key_list, 0, key)
        self.redis.set(key, value)
        self.redis.rpush(self.key_list, key)

    def contains(self, key: str) -> bool:
        return self.redis.exists(key) == 1

    def get_cache_stats(self):
        hits = int(self.redis.get(self.hits_key) or 0)
        misses = int(self.redis.get(self.misses_key) or 0)
        return {"hits": hits, "misses": misses}

    def items(self):
        keys = self.redis.lrange(self.key_list, 0, -1)
        items = []
        for key in keys:
            key_str = key.decode('utf-8')
            value = self.redis.get(key_str)
            if value is not None:
                items.append((key_str, value.decode('utf-8')))
        return items

    def clear(self):
        # Delete all keys related to this cache instance
        keys = self.redis.lrange(self.key_list, 0, -1)
        if keys:
            self.redis.delete(*keys)
        self.redis.delete(self.key_list)
        # Reset hits and misses counters in Redis
        self.redis.set(self.hits_key, 0)
        self.redis.set(self.misses_key, 0)

    def __str__(self):
        keys = self.redis.lrange(self.key_list, 0, -1)
        return str([key.decode('utf-8') for key in keys])
