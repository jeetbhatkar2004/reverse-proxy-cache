import unittest
from cache.lfu_cache import LFUCache

class TestLFUCache(unittest.TestCase):

    def test_put_get(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        self.assertEqual(cache.get(1), 1)
        cache.put(3, 3)
        self.assertEqual(cache.get(2), -1)  # 2 should be evicted
        self.assertEqual(cache.get(3), 3)

    def test_eviction(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.put(3, 3)
        self.assertEqual(cache.get(1), -1)  # 1 should be evicted

if __name__ == '__main__':
    unittest.main()
