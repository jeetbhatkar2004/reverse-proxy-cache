import redis
import json

class ARCCache:
    def __init__(self, capacity: int, host='localhost', port=6379, db=0):
        self.capacity = capacity
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.p = 0  # Target size for t1
        self.hits = 0
        self.misses = 0

    def _get_list(self, list_name):
        return json.loads(self.redis.get(list_name) or '[]')

    def _set_list(self, list_name, list_data):
        self.redis.set(list_name, json.dumps(list_data))

    def get(self, key: str) -> str:
        t1 = self._get_list('t1')
        t2 = self._get_list('t2')

        if key in t1:
            self.hits += 1
            t1.remove(key)
            t2.append(key)
            self._set_list('t1', t1)
            self._set_list('t2', t2)
            return self.redis.get(f'value:{key}')
        elif key in t2:
            self.hits += 1
            t2.remove(key)
            t2.append(key)
            self._set_list('t2', t2)
            return self.redis.get(f'value:{key}')
        self.misses += 1
        return -1

    def put(self, key: str, value: str) -> None:
        t1 = self._get_list('t1')
        t2 = self._get_list('t2')
        b1 = self._get_list('b1')
        b2 = self._get_list('b2')

        if key in t1 or key in t2:
            self.hits += 1
            if key in t1:
                t1.remove(key)
            else:
                t2.remove(key)
            t2.append(key)
        elif key in b1:
            self.p = min(self.capacity, self.p + max(1, len(b2)//len(b1)))
            self._replace(key)
            b1.remove(key)
            t2.append(key)
        elif key in b2:
            self.p = max(0, self.p - max(1, len(b1)//len(b2)))
            self._replace(key)
            b2.remove(key)
            t2.append(key)
        else:
            self.misses += 1
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

        self.redis.set(f'value:{key}', value)
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
        else:
            old_key = t2.pop(0)
            b2.append(old_key)

        self._set_list('t1', t1)
        self._set_list('t2', t2)
        self._set_list('b1', b1)
        self._set_list('b2', b2)

    def contains(self, key: str) -> bool:
        return self.redis.exists(f'value:{key}')

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return f"T1: {self._get_list('t1')}, T2: {self._get_list('t2')}, B1: {self._get_list('b1')}, B2: {self._get_list('b2')}, P: {self.p}"