import redis

class ARCCache:
    def __init__(self, capacity: int, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.capacity = capacity
        self.p = 0  # Target size for the T1 list
        
        # Keys for Redis data structures
        self.key_t1 = f"arc_cache_t1_{id(self)}"
        self.key_t2 = f"arc_cache_t2_{id(self)}"
        self.key_b1 = f"arc_cache_b1_{id(self)}"
        self.key_b2 = f"arc_cache_b2_{id(self)}"
        self.key_data = f"arc_cache_data_{id(self)}"
        self.hits_key = f"cache_hits_{id(self)}"
        self.misses_key = f"cache_misses_{id(self)}"

    def get(self, key: str) -> str:
        if not self.redis.hexists(self.key_data, key):
            # Increment misses atomically in Redis
            self.redis.incr(self.misses_key)
            return -1

        # Increment hits atomically in Redis
        self.redis.incr(self.hits_key)

        if self.redis.sismember(self.key_t1, key):
            self.redis.smove(self.key_t1, self.key_t2, key)
        elif self.redis.sismember(self.key_b1, key):
            self.p = min(self.capacity, self.p + max(1, self.redis.scard(self.key_b2) // self.redis.scard(self.key_b1)))
            self._replace(key)
            self.redis.smove(self.key_b1, self.key_t2, key)
        elif self.redis.sismember(self.key_b2, key):
            self.p = max(0, self.p - max(1, self.redis.scard(self.key_b1) // self.redis.scard(self.key_b2)))
            self._replace(key)
            self.redis.smove(self.key_b2, self.key_t2, key)

        return self.redis.hget(self.key_data, key).decode('utf-8')

    def put(self, key: str, value: str) -> None:
        if self.redis.hexists(self.key_data, key):
            self.redis.hset(self.key_data, key, value)
            self.get(key)  # Update cache state
            return

        if self.redis.scard(self.key_t1) + self.redis.scard(self.key_b1) == self.capacity:
            if self.redis.scard(self.key_t1) < self.capacity:
                self.redis.spop(self.key_b1)
                self._replace(key)
            else:
                lru_key = self.redis.spop(self.key_t1)
                self.redis.hdel(self.key_data, lru_key)
                self.redis.sadd(self.key_b1, lru_key)
        elif self.redis.scard(self.key_t1) + self.redis.scard(self.key_t2) + self.redis.scard(self.key_b1) + self.redis.scard(self.key_b2) >= self.capacity:
            if self.redis.scard(self.key_t1) + self.redis.scard(self.key_t2) + self.redis.scard(self.key_b1) + self.redis.scard(self.key_b2) >= 2 * self.capacity:
                self.redis.spop(self.key_b2)
            self._replace(key)

        self.redis.hset(self.key_data, key, value)
        self.redis.sadd(self.key_t1, key)

    def _replace(self, key: str):
        if self.redis.scard(self.key_t1) >= 1 and (self.redis.scard(self.key_t1) > self.p or (self.redis.sismember(self.key_b2, key) and self.redis.scard(self.key_t1) == self.p)):
            lru_key = self.redis.spop(self.key_t1)
            self.redis.sadd(self.key_b1, lru_key)
        else:
            lru_key = self.redis.spop(self.key_t2)
            self.redis.sadd(self.key_b2, lru_key)
        self.redis.hdel(self.key_data, lru_key)

    def contains(self, key: str) -> bool:
        return self.redis.hexists(self.key_data, key)

    def get_cache_stats(self):
        hits = int(self.redis.get(self.hits_key) or 0)
        misses = int(self.redis.get(self.misses_key) or 0)
        return {"hits": hits, "misses": misses}

    def items(self):
        return [(k.decode('utf-8'), v.decode('utf-8')) for k, v in self.redis.hgetall(self.key_data).items()]

    def clear(self):
        self.redis.delete(self.key_t1, self.key_t2, self.key_b1, self.key_b2, self.key_data)
        self.redis.set(self.hits_key, 0)
        self.redis.set(self.misses_key, 0)
        self.p = 0

    def __str__(self):
        return str(dict(self.items()))