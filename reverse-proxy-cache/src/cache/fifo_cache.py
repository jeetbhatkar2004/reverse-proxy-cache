import redis

class FIFOCache:
    def __init__(self, capacity: int, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
        self.key_list = 'fifo_keys'

    def get(self, key: str) -> str:
        if not self.redis.exists(key):
            self.misses += 1
            return -1
        self.hits += 1
        return self.redis.get(key)

    def put(self, key: str, value: str) -> None:
        if not self.redis.exists(key):
            self.misses += 1
            if self.redis.llen(self.key_list) >= self.capacity:
                oldest_key = self.redis.lpop(self.key_list)
                self.redis.delete(oldest_key)
        else:
            self.hits += 1
        self.redis.set(key, value)
        self.redis.rpush(self.key_list, key)

    def contains(self, key: str) -> bool:
        return self.redis.exists(key)

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return str(self.redis.lrange(self.key_list, 0, -1))