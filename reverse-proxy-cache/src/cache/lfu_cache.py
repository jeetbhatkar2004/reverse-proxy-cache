from collections import defaultdict, OrderedDict

class LFUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.min_freq = 0
        self.freq_map = defaultdict(OrderedDict)
        self.key_map = {}

    def _update(self, key: int, value: int = None) -> None:
        freq = self.key_map[key][1]
        value = self.key_map[key][0] if value is None else value

        del self.freq_map[freq][key]
        if not self.freq_map[freq]:
            del self.freq_map[freq]
            if freq == self.min_freq:
                self.min_freq += 1

        self.freq_map[freq + 1][key] = value
        self.key_map[key] = (value, freq + 1)

    def get(self, key: int) -> int:
        if key not in self.key_map:
            return -1
        self._update(key)
        return self.key_map[key][0]

    def put(self, key: int, value: int) -> None:
        if self.capacity == 0:
            return

        if key in self.key_map:
            self._update(key, value)
        else:
            if len(self.key_map) >= self.capacity:
                lfu_key, _ = self.freq_map[self.min_freq].popitem(last=False)
                del self.key_map[lfu_key]
            self.freq_map[1][key] = value
            self.key_map[key] = (value, 1)
            self.min_freq = 1

    def contains(self, key: int) -> bool:
        return key in self.key_map

    def __str__(self):
        return str(self.key_map)
