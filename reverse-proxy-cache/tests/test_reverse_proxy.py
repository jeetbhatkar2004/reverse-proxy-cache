import unittest
import asyncio
from server.reverse_proxy import ReverseProxy
from cache.lru_cache import LRUCache

class TestReverseProxy(unittest.TestCase):

    def setUp(self):
        self.cache = LRUCache(2)
        self.urls = ['https://httpbin.org/get']
        self.proxy = ReverseProxy(self.cache, self.urls)

    def test_fetch(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.proxy.run())
        self.assertIn('https://httpbin.org/get', self.cache)

if __name__ == '__main__':
    unittest.main()
