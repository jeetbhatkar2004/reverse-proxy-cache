from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.hits = 0  # Counter for cache hits
        self.misses = 0  # Counter for cache misses

    def get(self, key: str) -> str:
        if key not in self.cache:
            self.misses += 1
            return -1  # or None if you prefer
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]

    def put(self, key: str, value: str) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            self.misses += 1
        self.cache[key] = value

        if len(self.cache) > self.capacity:
            evicted_key, _ = self.cache.popitem(last=False)

    def contains(self, key: str) -> bool:
        return key in self.cache

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return str(self.cache)
