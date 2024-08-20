import random

class RRCache:
    def __init__(self, capacity: int):
        self.cache = {}
        self.capacity = capacity
        self.keys = []  # To keep track of keys for random eviction

    def get(self, key: str) -> str:
        return self.cache.get(key, -1)  # Return -1 or None if key not found

    def put(self, key: str, value: str) -> None:
        if key in self.cache:
            self.cache[key] = value  # Update the value if key is already in cache
        else:
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

    def __str__(self):
        return str(self.cache)
