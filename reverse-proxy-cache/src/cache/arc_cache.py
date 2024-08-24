from collections import OrderedDict

class ARCCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.t1 = OrderedDict()  # LRU for recently accessed items
        self.t2 = OrderedDict()  # LRU for frequently accessed items
        self.b1 = OrderedDict()  # Ghost list for recently evicted from t1
        self.b2 = OrderedDict()  # Ghost list for recently evicted from t2
        self.p = 0  # Target size for t1
        self.hits = 0  # Counter for cache hits
        self.misses = 0  # Counter for cache misses

    def get(self, key: str) -> str:
        if key in self.t1:
            self.hits += 1
            value = self.t1.pop(key)
            self.t2[key] = value  # Move to t2 since it's now a frequent item
            return value
        elif key in self.t2:
            self.hits += 1
            self.t2.move_to_end(key)  # Move to the end of t2
            return self.t2[key]
        self.misses += 1
        return -1  # Key not found

    def put(self, key: str, value: str) -> None:
        if key in self.t1 or key in self.t2:
            self.hits += 1
            if key in self.t1:
                self.t1.pop(key)
            else:
                self.t2.pop(key)
            self.t2[key] = value  # Move to t2 since it's now a frequent item
        elif key in self.b1:
            self._adapt(len(self.b1) / (len(self.b1) + len(self.b2)))
            self._replace(key)
            self.b1.pop(key)
            self.t2[key] = value
        elif key in self.b2:
            self._adapt(len(self.b2) / (len(self.b1) + len(self.b2)))
            self._replace(key)
            self.b2.pop(key)
            self.t2[key] = value
        else:
            self.misses += 1
            if len(self.t1) + len(self.t2) >= self.capacity:
                if len(self.t1) < self.capacity:
                    if len(self.t1) + len(self.b1) >= self.capacity:
                        self.b1.popitem(last=False)
                    self._replace(key)
                else:
                    self.t1.popitem(last=False)
            else:
                total = len(self.t1) + len(self.b1) + len(self.t2) + len(self.b2)
                if total >= self.capacity:
                    if total == 2 * self.capacity:
                        self.b2.popitem(last=False)
                    self._replace(key)
            self.t1[key] = value

    def _replace(self, key: str) -> None:
        if self.t1 and (len(self.t1) > self.p or (key in self.b2 and len(self.t1) == self.p)):
            old_key, old_value = self.t1.popitem(last=False)
            self.b1[old_key] = old_value
        else:
            old_key, old_value = self.t2.popitem(last=False)
            self.b2[old_key] = old_value

    def _adapt(self, delta: float) -> None:
        self.p = min(self.capacity, max(0, self.p + delta))

    def contains(self, key: str) -> bool:
        return key in self.t1 or key in self.t2

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return f"T1: {self.t1}, T2: {self.t2}, B1: {self.b1}, B2: {self.b2}, P: {self.p}"