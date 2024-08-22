from collections import OrderedDict

class FIFOCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.hits = 0  # Counter for cache hits
        self.misses = 0  # Counter for cache misses

    def get(self, key: str) -> str:
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return -1  # Return -1 or None if key not found

    def put(self, key: str, value: str) -> None:
        if key not in self.cache:
            self.misses += 1

        self.cache[key] = value  # Insert/Update the value in the cache

        if len(self.cache) > self.capacity:
            evicted_key, _ = self.cache.popitem(last=False)  # Evict the oldest item (first in)

    def contains(self, key: str) -> bool:
        return key in self.cache  # Return True if key is in cache, else False

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return str(self.cache)
