import asyncio
import aiohttp
from cache.lru_cache import LRUCache
from cache.lfu_cache import LFUCache
from cache.fifo_cache import FIFOCache
from cache.arc_cache import ARCCache
from cache.rr_cache import RRCache

from server.reverse_proxy import ReverseProxy

# Choose the cache strategy
cache_capacity = 32
urls = [
    'http://example.com',
    'https://httpbin.org/get',
    'https://jsonplaceholder.typicode.com/posts/1',
    'https://jsonplaceholder.typicode.com/comments/1',
    'https://jsonplaceholder.typicode.com/albums/1',
    'https://jsonplaceholder.typicode.com/photos/1',
    'https://jsonplaceholder.typicode.com/todos/1',
    'https://jsonplaceholder.typicode.com/users/1',
    'https://jsonplaceholder.typicode.com/posts/2',
    'https://jsonplaceholder.typicode.com/comments/2',
    'https://jsonplaceholder.typicode.com/albums/2',
    'https://jsonplaceholder.typicode.com/photos/2',
    'https://jsonplaceholder.typicode.com/todos/2',
    'https://jsonplaceholder.typicode.com/users/2',
    'https://jsonplaceholder.typicode.com/posts/3',
    'https://jsonplaceholder.typicode.com/comments/3',
    'https://jsonplaceholder.typicode.com/albums/3',
    'https://jsonplaceholder.typicode.com/photos/3',
    'https://jsonplaceholder.typicode.com/todos/3',
    'https://jsonplaceholder.typicode.com/users/3',
    'https://jsonplaceholder.typicode.com/posts/1',  # Cache hit
    'https://jsonplaceholder.typicode.com/comments/1',  # Cache hit
    'https://jsonplaceholder.typicode.com/albums/2',  # Cache hit
    'https://jsonplaceholder.typicode.com/photos/2',  # Cache hit
    'https://jsonplaceholder.typicode.com/users/1',  # Cache hit
    'https://jsonplaceholder.typicode.com/posts/3',  # Cache hit
    'https://jsonplaceholder.typicode.com/comments/3',  # Cache hit
    'https://jsonplaceholder.typicode.com/albums/3',  # Cache hit
    'https://httpbin.org/get',  # Cache hit
    'https://example.com',  # Cache hit
]

cache_strategy = "LRU"  # or "LFU"

if cache_strategy == "LRU":
    cache = LRUCache(capacity=cache_capacity)
elif cache_strategy == "LFU":
    cache = LFUCache(capacity=cache_capacity)
elif cache_strategy == "FIFO":
    cache = FIFOCache(capacity = cache_capacity)
elif cache_strategy == "ARC":
    cache = ARCCache(capacity=cache_capacity)
elif cache_strategy == "RR":
    cache = RRCache(capacity=cache_capacity)
proxy = ReverseProxy(cache, urls)

async def main():
    async with aiohttp.ClientSession() as session:
        proxy = ReverseProxy(cache, urls)
        proxy.session = session
        for url in urls:
            await proxy.fetch(url)

asyncio.run(main())


