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
            value = self.t1.pop(key)
            self.t2[key] = value  # Move to t2 since it's now a frequent item
            self.hits += 1
            return value
        elif key in self.t2:
            value = self.t2[key]  # Access from t2 doesn't change anything
            self.hits += 1
            return value
        self.misses += 1
        return -1  # Key not found

    def put(self, key: str, value: str) -> None:
        if key in self.t1:
            self.t1.pop(key)
            self.t2[key] = value  # Move to t2 since it's now a frequent item
        elif key in self.t2:
            self.t2[key] = value  # Update the value in t2
        elif key in self.b1:
            # Case where the item was in b1 (t1 ghost), increase p
            self._adapt(True)
            self._replace(key, value)
            self.b1.pop(key)
            self.t2[key] = value
        elif key in self.b2:
            # Case where the item was in b2 (t2 ghost), decrease p
            self._adapt(False)
            self._replace(key, value)
            self.b2.pop(key)
            self.t2[key] = value
        else:
            # New item case
            if len(self.t1) + len(self.b1) == self.capacity:
                if len(self.t1) < self.capacity:
                    self.b1.popitem(last=False)
                    self._replace(key, value)
                else:
                    self.t1.popitem(last=False)
            elif len(self.t1) + len(self.b1) + len(self.t2) + len(self.b2) >= self.capacity:
                if len(self.t1) + len(self.b1) + len(self.t2) + len(self.b2) == 2 * self.capacity:
                    self.b2.popitem(last=False)
            self.t1[key] = value

    def _replace(self, key: str, value: str) -> None:
        if len(self.t1) > 0 and (len(self.t1) > self.p or (key in self.b2 and len(self.t1) == self.p)):
            evicted_key, evicted_value = self.t1.popitem(last=False)
            self.b1[evicted_key] = evicted_value  # Add to ghost list b1
        else:
            evicted_key, evicted_value = self.t2.popitem(last=False)
            self.b2[evicted_key] = evicted_value  # Add to ghost list b2

    def _adapt(self, increase: bool) -> None:
        if increase:
            self.p = min(self.capacity, self.p + max(1, len(self.b2) // len(self.b1)))
        else:
            self.p = max(0, self.p - max(1, len(self.b1) // len(self.b2)))

    def contains(self, key: str) -> bool:
        return key in self.t1 or key in self.t2

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return f"T1: {self.t1}, T2: {self.t2}, B1: {self.b1}, B2: {self.b2}, P: {self.p}"
