import redis
import time

class LFUCache:
    def __init__(self, capacity: int, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.capacity = capacity
        self.key_frequency = f"lfu_cache_frequency_{id(self)}"
        self.key_last_access = f"lfu_cache_last_access_{id(self)}"
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
            # Increase frequency
            self.redis.zincrby(self.key_frequency, 1, key)
            # Update last access time
            current_time = time.time()
            self.redis.zadd(self.key_last_access, {key: current_time})
            return value.decode('utf-8')

    def put(self, key: str, value: str) -> None:
        if not self.contains(key):
            cache_size = self.redis.zcard(self.key_frequency)
            if cache_size >= self.capacity:
                self._evict()

        self.redis.set(key, value)
        # Initialize or increase frequency
        self.redis.zincrby(self.key_frequency, 1, key)
        # Update last access time
        current_time = time.time()
        self.redis.zadd(self.key_last_access, {key: current_time})

    def _evict(self):
        # Get the lowest frequency
        min_frequency = self.redis.zrange(self.key_frequency, 0, 0, withscores=True)[0][1]
        # Get all items with the lowest frequency
        items_to_evict = self.redis.zrangebyscore(self.key_frequency, min_frequency, min_frequency)
        if len(items_to_evict) > 1:
            # If there are multiple items with the lowest frequency, evict the least recently used
            oldest = self.redis.zrange(self.key_last_access, 0, 0, withscores=True, byscore=False)
            if oldest:
                oldest_key = oldest[0][0]
                self.redis.delete(oldest_key)
                self.redis.zrem(self.key_frequency, oldest_key)
                self.redis.zrem(self.key_last_access, oldest_key)
        else:
            # If there's only one item with the lowest frequency, evict it
            key_to_evict = items_to_evict[0]
            self.redis.delete(key_to_evict)
            self.redis.zrem(self.key_frequency, key_to_evict)
            self.redis.zrem(self.key_last_access, key_to_evict)

    def contains(self, key: str) -> bool:
        return self.redis.exists(key) == 1

    def get_cache_stats(self):
        # Retrieve hits and misses from Redis
        hits = int(self.redis.get(self.hits_key) or 0)
        misses = int(self.redis.get(self.misses_key) or 0)
        return {"hits": hits, "misses": misses}

    def items(self):
        keys = self.redis.zrange(self.key_frequency, 0, -1)
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