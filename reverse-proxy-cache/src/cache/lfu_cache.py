import redis
import json

class LFUCache:
    def __init__(self, capacity: int, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.capacity = capacity
        self.min_freq = 0
        self.hits = 0
        self.misses = 0

    def _update(self, key: str, value: str = None) -> None:
        freq = int(self.redis.hget('freq_map', key) or 0)
        value = value or self.redis.get(key)

        self.redis.zrem(f'freq:{freq}', key)
        if self.redis.zcard(f'freq:{freq}') == 0 and freq == self.min_freq:
            self.min_freq += 1

        self.redis.zadd(f'freq:{freq+1}', {key: 0})
        self.redis.hset('freq_map', key, freq + 1)
        self.redis.set(key, value)

    def get(self, key: str) -> str:
        if not self.redis.exists(key):
            self.misses += 1
            return -1
        self._update(key)
        self.hits += 1
        return self.redis.get(key)

    def put(self, key: str, value: str) -> None:
        if self.capacity == 0:
            return

        if self.redis.exists(key):
            self._update(key, value)
            self.hits += 1
        else:
            self.misses += 1
            if self.redis.dbsize() >= self.capacity:
                lfu_key = self.redis.zrange(f'freq:{self.min_freq}', 0, 0)[0]
                self.redis.zrem(f'freq:{self.min_freq}', lfu_key)
                self.redis.delete(lfu_key)
                self.redis.hdel('freq_map', lfu_key)

            self.redis.zadd('freq:1', {key: 0})
            self.redis.hset('freq_map', key, 1)
            self.redis.set(key, value)
            self.min_freq = 1

    def contains(self, key: str) -> bool:
        return self.redis.exists(key)

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return str(self.redis.keys())