import redis

class LRUCache:
    def __init__(self, capacity: int, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
        self.key_list = 'lru_keys'

    def get(self, key: str) -> str:
        if not self.redis.exists(key):
            self.misses += 1
            return -1
        self.redis.lrem(self.key_list, 0, key)
        self.redis.rpush(self.key_list, key)
        self.hits += 1
        return self.redis.get(key)

    def put(self, key: str, value: str) -> None:
        if self.redis.exists(key):
            self.redis.lrem(self.key_list, 0, key)
            self.hits += 1
        else:
            self.misses += 1
            if self.redis.llen(self.key_list) >= self.capacity:
                lru_key = self.redis.lpop(self.key_list)
                self.redis.delete(lru_key)
        self.redis.rpush(self.key_list, key)
        self.redis.set(key, value)

    def contains(self, key: str) -> bool:
        return self.redis.exists(key)

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return str(self.redis.lrange(self.key_list, 0, -1))