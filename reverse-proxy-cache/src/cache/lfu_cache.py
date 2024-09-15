import redis

class LFUCache:
    def __init__(self, capacity: int, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.capacity = capacity
        self.min_freq = 0
        self.hits_key = f"cache_hits_{id(self)}"
        self.misses_key = f"cache_misses_{id(self)}"
        self.cache_prefix = f"lfu_cache_{id(self)}"

    # ... rest of the class remains the same ...


    def _update(self, key: str, value: str = None) -> None:
        freq = int(self.redis.hget(f"{self.cache_prefix}:freq_map", key) or 0)
        value = value or self.redis.get(f"{self.cache_prefix}:value:{key}")

        self.redis.zrem(f"{self.cache_prefix}:freq:{freq}", key)
        if self.redis.zcard(f"{self.cache_prefix}:freq:{freq}") == 0 and freq == self.min_freq:
            self.min_freq += 1

        self.redis.zadd(f"{self.cache_prefix}:freq:{freq+1}", {key: 0})
        self.redis.hset(f"{self.cache_prefix}:freq_map", key, freq + 1)
        self.redis.set(f"{self.cache_prefix}:value:{key}", value)

    def get(self, key: str) -> str:
        if not self.redis.exists(f"{self.cache_prefix}:value:{key}"):
            self.redis.incr(self.misses_key)
            return -1
        self._update(key)
        self.redis.incr(self.hits_key)
        value = self.redis.get(f"{self.cache_prefix}:value:{key}")
        return value.decode('utf-8') if value else -1

    def put(self, key: str, value: str) -> None:
        if self.capacity == 0:
            return

        if self.redis.exists(f"{self.cache_prefix}:value:{key}"):
            self._update(key, value)
            self.redis.incr(self.hits_key)
        else:
            self.redis.incr(self.misses_key)
            if self.redis.hlen(f"{self.cache_prefix}:freq_map") >= self.capacity:
                lfu_keys = self.redis.zrange(f"{self.cache_prefix}:freq:{self.min_freq}", 0, 0)
                if lfu_keys:
                    lfu_key = lfu_keys[0]
                    self.redis.zrem(f"{self.cache_prefix}:freq:{self.min_freq}", lfu_key)
                    self.redis.delete(f"{self.cache_prefix}:value:{lfu_key}")
                    self.redis.hdel(f"{self.cache_prefix}:freq_map", lfu_key)

            self.redis.zadd(f"{self.cache_prefix}:freq:1", {key: 0})
            self.redis.hset(f"{self.cache_prefix}:freq_map", key, 1)
            self.redis.set(f"{self.cache_prefix}:value:{key}", value)
            self.min_freq = 1

    def contains(self, key: str) -> bool:
        return self.redis.exists(f"{self.cache_prefix}:value:{key}") == 1

    def get_cache_stats(self):
        hits = int(self.redis.get(self.hits_key) or 0)
        misses = int(self.redis.get(self.misses_key) or 0)
        return {"hits": hits, "misses": misses}

    def items(self):
        keys = self.redis.hkeys(f"{self.cache_prefix}:freq_map")
        items = []
        for key in keys:
            key_str = key.decode('utf-8')
            value = self.redis.get(f"{self.cache_prefix}:value:{key_str}")
            if value is not None:
                items.append((key_str, value.decode('utf-8')))
        return items
    def clear(self):
        # Flush the entire Redis database used by this cache
        self.redis.flushdb()
        # Reset hits and misses counters in Redis
        self.redis.set(self.hits_key, 0)
        self.redis.set(self.misses_key, 0)

    def __str__(self):
        keys = self.redis.hkeys(f"{self.cache_prefix}:freq_map")
        return str([key.decode('utf-8') for key in keys])
