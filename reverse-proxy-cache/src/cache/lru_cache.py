from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.hits = 0  # Counter for cache hits
        self.misses = 0  # Counter for cache misses

    def get(self, key: str) -> str:
        if key not in self.cache:
            self.misses += 1  # Increment misses when the key is not found
            return -1  # or None if you prefer
        self.cache.move_to_end(key)
        self.hits += 1  # Increment hits when the key is found
        return self.cache[key]

    def put(self, key: str, value: str) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1  # Increment hits when updating an existing key
        else:
            self.misses += 1  # Increment misses when adding a new key
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)  # Evict the least recently used item
        self.cache[key] = value

    def contains(self, key: str) -> bool:
        return key in self.cache

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return str(self.cache)