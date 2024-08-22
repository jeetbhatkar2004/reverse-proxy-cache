import random

class RRCache:
    def __init__(self, capacity: int):
        self.cache = {}
        self.capacity = capacity
        self.keys = []  # To keep track of keys for random eviction
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
        if key in self.cache:
            self.cache[key] = value  # Update the value if key is already in cache
        else:
            self.misses += 1
            if len(self.cache) >= self.capacity:
                # Randomly select a key to evict
                random_key = random.choice(self.keys)
                self.keys.remove(random_key)
                del self.cache[random_key]

            # Insert the new key-value pair
            self.cache[key] = value
            self.keys.append(key)

    def contains(self, key: str) -> bool:
        return key in self.cache  # Return True if key is in cache, else False

    def get_cache_stats(self):
        return {"hits": self.hits, "misses": self.misses}

    def __str__(self):
        return str(self.cache)
