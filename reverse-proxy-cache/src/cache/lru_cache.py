from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.addition_counter = 0  # Counter to track the number of additions

    def get(self, key: str) -> str:
        if key not in self.cache:
            return -1  # or None if you prefer
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: str) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        self.addition_counter += 1  # Increment the counter after each addition

        if len(self.cache) > self.capacity:
            evicted_key, _ = self.cache.popitem(last=False)

    def contains(self, key: str) -> bool:
        if key in self.cache:
            return True
        return False

    def __str__(self):
        return str(self.cache)
