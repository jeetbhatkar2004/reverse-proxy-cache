import random

class RRCache:
    def __init__(self, capacity: int):
        self.cache = {}
        self.capacity = capacity
        self.hits = 0  # Counter for cache hits
        self.misses = 0  # Counter for cache misses

    def get(self, key: str) -> str:
        if key not in self.cache:
            self.misses += 1  # Increment misses when the key is not found
            return -1  # or None if you prefer
        self.hits += 1  # Increment hits when the key is found
        return self.cache[key]

    def put(self, key: str, value: str) -> None:
        if key not in self.cache:
            self.misses += 1  # Since we're inserting, it was a miss before
            if len(self.cache) >= self.capacity:
                # Randomly select a key to evict
                random_key = random.choice(list(self.cache.keys()))
                del self.cache[random_key]
        else:
            self.hits += 1  # If the key exists, it's a hit
        self.cache[key] = value

    def contains(self, key: str) -> bool:
        return key in self.cache

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return str(self.cache)