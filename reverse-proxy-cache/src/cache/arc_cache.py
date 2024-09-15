import redis
import json

class ARCCache:
    def __init__(self, capacity: int, redis_host='localhost', redis_port=6379, redis_db=0):
        self.capacity = capacity
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.p = 0  # Target size for t1
        self.hits_key = f"cache_hits_{id(self)}"
        self.misses_key = f"cache_misses_{id(self)}"
        self.cache_prefix = f"arc_cache_{id(self)}"

    def _get_list(self, list_name):
        data = self.redis.get(f"{self.cache_prefix}:{list_name}")
        return json.loads(data) if data else []

    def _set_list(self, list_name, list_data):
        self.redis.set(f"{self.cache_prefix}:{list_name}", json.dumps(list_data))

    def get(self, key: str) -> str:
        t1 = self._get_list('t1')
        t2 = self._get_list('t2')

        if key in t1:
            # Increment hits atomically in Redis
            self.redis.incr(self.hits_key)
            t1.remove(key)
            t2.append(key)
            self._set_list('t1', t1)
            self._set_list('t2', t2)
            value = self.redis.get(f"{self.cache_prefix}:value:{key}")
            return value.decode('utf-8') if value else -1
        elif key in t2:
            # Increment hits atomically in Redis
            self.redis.incr(self.hits_key)
            t2.remove(key)
            t2.append(key)
            self._set_list('t2', t2)
            value = self.redis.get(f"{self.cache_prefix}:value:{key}")
            return value.decode('utf-8') if value else -1
        else:
            # Increment misses atomically in Redis
            self.redis.incr(self.misses_key)
            return -1

    def put(self, key: str, value: str) -> None:
        t1 = self._get_list('t1')
        t2 = self._get_list('t2')
        b1 = self._get_list('b1')
        b2 = self._get_list('b2')

        if key in t1 or key in t2:
            # Increment hits atomically in Redis
            self.redis.incr(self.hits_key)
            if key in t1:
                t1.remove(key)
            else:
                t2.remove(key)
            t2.append(key)
        elif key in b1:
            self.p = min(self.capacity, self.p + max(1, len(b2) // max(1, len(b1))))
            self._replace(key)
            b1.remove(key)
            t2.append(key)
        elif key in b2:
            self.p = max(0, self.p - max(1, len(b1) // max(1, len(b2))))
            self._replace(key)
            b2.remove(key)
            t2.append(key)
        else:
            # Increment misses atomically in Redis
            self.redis.incr(self.misses_key)
            if len(t1) + len(t2) >= self.capacity:
                if len(t1) < self.capacity:
                    if len(t1) + len(b1) >= self.capacity:
                        b1.pop(0)
                    self._replace(key)
                else:
                    removed = t1.pop(0)
                    b1.append(removed)
            else:
                total = len(t1) + len(b1) + len(t2) + len(b2)
                if total >= self.capacity:
                    if total == 2 * self.capacity:
                        b2.pop(0)
                    self._replace(key)
            t1.append(key)

        self.redis.set(f"{self.cache_prefix}:value:{key}", value)
        self._set_list('t1', t1)
        self._set_list('t2', t2)
        self._set_list('b1', b1)
        self._set_list('b2', b2)

    def _replace(self, key: str) -> None:
        t1 = self._get_list('t1')
        t2 = self._get_list('t2')
        b1 = self._get_list('b1')
        b2 = self._get_list('b2')

        if t1 and (len(t1) > self.p or (key in b2 and len(t1) == self.p)):
            old_key = t1.pop(0)
            b1.append(old_key)
            # Remove the old key's value from Redis
            self.redis.delete(f"{self.cache_prefix}:value:{old_key}")
        else:
            old_key = t2.pop(0)
            b2.append(old_key)
            # Remove the old key's value from Redis
            self.redis.delete(f"{self.cache_prefix}:value:{old_key}")

        self._set_list('t1', t1)
        self._set_list('t2', t2)
        self._set_list('b1', b1)
        self._set_list('b2', b2)

    def contains(self, key: str) -> bool:
        return self.redis.exists(f"{self.cache_prefix}:value:{key}") == 1

    def get_cache_stats(self):
        hits = int(self.redis.get(self.hits_key) or 0)
        misses = int(self.redis.get(self.misses_key) or 0)
        return {"hits": hits, "misses": misses}

    def items(self):
        t1 = self._get_list('t1')
        t2 = self._get_list('t2')
        all_keys = t1 + t2
        items = []
        for key in all_keys:
            value = self.redis.get(f"{self.cache_prefix}:value:{key}")
            if value is not None:
                items.append((key, value.decode('utf-8')))
        return items

    def clear(self):
        # Delete all keys related to this cache instance
        keys = self.redis.keys(f"{self.cache_prefix}:*")
        if keys:
            self.redis.delete(*keys)
        # Reset hits and misses counters in Redis
        self.redis.set(self.hits_key, 0)
        self.redis.set(self.misses_key, 0)
        self.p = 0  # Reset target size

    def __str__(self):
        return f"T1: {self._get_list('t1')}, T2: {self._get_list('t2')}, B1: {self._get_list('b1')}, B2: {self._get_list('b2')}, P: {self.p}"
