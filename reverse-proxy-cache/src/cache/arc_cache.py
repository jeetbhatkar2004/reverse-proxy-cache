import redis
import time

class ARCCache:
    def __init__(self, capacity: int, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.capacity = capacity
        self.p = 0  # Target size for the T1 cache
        
        # Define Redis keys for different parts of the cache
        self.t1 = f"arc_t1_{id(self)}"
        self.t2 = f"arc_t2_{id(self)}"
        self.b1 = f"arc_b1_{id(self)}"
        self.b2 = f"arc_b2_{id(self)}"
        self.key_prefix = f"arc_data_{id(self)}"
        self.p_key = f"arc_p_{id(self)}"
        
        self.hits_key = f"cache_hits_{id(self)}"
        self.misses_key = f"cache_misses_{id(self)}"

    def get(self, key: str) -> str:
        full_key = f"{self.key_prefix}:{key}"
        value = self.redis.get(full_key)
        
        if value is None:
            self.redis.incr(self.misses_key)
            if self.redis.sismember(self.b1, key):
                self._adjust_p(True)
                self._move(self.b1, self.t2, key)
            elif self.redis.sismember(self.b2, key):
                self._adjust_p(False)
                self._move(self.b2, self.t2, key)
            return -1
        else:
            self.redis.incr(self.hits_key)
            if self.redis.sismember(self.t1, key):
                self._move(self.t1, self.t2, key)
            elif self.redis.sismember(self.t2, key):
                self.redis.zadd(self.t2, {key: time.time()})
            return value.decode('utf-8')

    def put(self, key: str, value: str) -> None:
        full_key = f"{self.key_prefix}:{key}"
        
        if self.redis.get(full_key) is not None:
            self.redis.set(full_key, value)
            self.get(key)  # This will move the key to T2 if it's in T1
        else:
            if self._cache_size() >= self.capacity:
                self._replace(key)
            
            if self.redis.sismember(self.b1, key):
                self.p = min(self.capacity, self.p + max(1, self.redis.zcard(self.b2) // self.redis.zcard(self.b1)))
            elif self.redis.sismember(self.b2, key):
                self.p = max(0, self.p - max(1, self.redis.zcard(self.b1) // self.redis.zcard(self.b2)))
            else:
                if (self.redis.zcard(self.t1) + self.redis.zcard(self.b1)) == self.capacity:
                    if self.redis.zcard(self.t1) < self.capacity:
                        self.redis.zpopmin(self.b1)
                        self._replace(key)
                    else:
                        self.redis.zpopmin(self.t1)
                elif (self.redis.zcard(self.t1) + self.redis.zcard(self.b1)) < self.capacity:
                    if self._cache_size() >= self.capacity:
                        if self._cache_size() >= 2 * self.capacity:
                            self.redis.zpopmin(self.b2)
                        else:
                            self._replace(key)
            
            self.redis.set(full_key, value)
            self.redis.zadd(self.t1, {key: time.time()})
        
        self.redis.set(self.p_key, self.p)

    def _cache_size(self):
        return self.redis.zcard(self.t1) + self.redis.zcard(self.t2)

    def _adjust_p(self, in_b1: bool):
        if in_b1:
            self.p = min(self.capacity, self.p + max(1, self.redis.zcard(self.b2) // self.redis.zcard(self.b1)))
        else:
            self.p = max(0, self.p - max(1, self.redis.zcard(self.b1) // self.redis.zcard(self.b2)))
        self.redis.set(self.p_key, self.p)

    def _replace(self, key: str):
        if self.redis.zcard(self.t1) > 0 and (self.redis.zcard(self.t1) > self.p or 
            (self.redis.sismember(self.b2, key) and self.redis.zcard(self.t1) == self.p)):
            old_key = self.redis.zpopmin(self.t1)[0][0].decode('utf-8')
            self.redis.zadd(self.b1, {old_key: time.time()})
        else:
            old_key = self.redis.zpopmin(self.t2)[0][0].decode('utf-8')
            self.redis.zadd(self.b2, {old_key: time.time()})
        self.redis.delete(f"{self.key_prefix}:{old_key}")

    def _move(self, source: str, dest: str, key: str):
        self.redis.zrem(source, key)
        self.redis.zadd(dest, {key: time.time()})

    def contains(self, key: str) -> bool:
        full_key = f"{self.key_prefix}:{key}"
        return self.redis.exists(full_key) == 1

    def get_cache_stats(self):
        hits = int(self.redis.get(self.hits_key) or 0)
        misses = int(self.redis.get(self.misses_key) or 0)
        return {"hits": hits, "misses": misses}

    def items(self):
        all_keys = self.redis.zunion([self.t1, self.t2])
        items = []
        for key in all_keys:
            full_key = f"{self.key_prefix}:{key.decode('utf-8')}"
            value = self.redis.get(full_key)
            if value is not None:
                items.append((key.decode('utf-8'), value.decode('utf-8')))
        return items

    def clear(self):
        self.redis.flushdb()
        self.redis.set(self.hits_key, 0)
        self.redis.set(self.misses_key, 0)
        self.p = 0
        self.redis.set(self.p_key, self.p)

    def __str__(self):
        items = self.items()
        return str(dict(items))