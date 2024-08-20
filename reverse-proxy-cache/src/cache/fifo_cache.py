from collections import OrderedDict

class FIFOCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.addition_counter = 0  # Counter to track the number of additions

    def get(self, key: str) -> str:
        return self.cache.get(key, -1)  # Return -1 or None if key not found

    def put(self, key: str, value: str) -> None:
        if key not in self.cache:
            self.addition_counter += 1  # Increment the counter if key is new

        self.cache[key] = value  # Insert/Update the value in the cache

        if len(self.cache) > self.capacity:
            evicted_key, _ = self.cache.popitem(last=False)  # Evict the oldest item (first in)

    def contains(self, key: str) -> bool:
        return key in self.cache  # Return True if key is in cache, else False

    def __str__(self):
        return str(self.cache)
