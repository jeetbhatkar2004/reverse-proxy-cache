import asyncio
import aiohttp
from collections import deque

class Node:
    def __init__(self, port):
        self.port = port
        self.current_url = None

class ReverseProxy:
    def __init__(self, cache, urls, num_nodes):
        self.cache = cache
        self.urls = deque(urls)
        self.nodes = [Node(8000 + i) for i in range(num_nodes)]
        self.lock = asyncio.Lock()
        self.processed_urls = set()
        self.total_urls = len(urls)

    async def process_urls(self):
        async with aiohttp.ClientSession() as session:
            self.session = session
            while self.urls:
                for node in self.nodes:
                    if not self.urls:
                        break
                    url = self.urls.popleft()
                    node.current_url = url
                    result = await self.fetch(url, node)
                    yield result
                    await asyncio.sleep(1)  # Simulate 1 second processing time
                    node.current_url = None
                    self.processed_urls.add(url)
                    
                    if len(self.processed_urls) >= self.total_urls:
                        return  # All URLs have been processed

    async def fetch(self, url, node):
        async with self.lock:
            if self.cache.contains(url):
                print(f"Cache hit for {url} on Node {node.port}")
                return ("Cache hit", self.cache.get(url), node.port)

        print(f"Cache miss for {url} on Node {node.port}")
        try:
            async with self.session.get(url, ssl=False, timeout=10) as response:
                content = await response.text()
                async with self.lock:
                    self.cache.put(url, content)
                return (f"Cache miss (Node {node.port})", content, node.port)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"Failed to fetch {url} on Node {node.port}: {e}")
            return (f"Error fetching {url}", None, node.port)

    def get_node_status(self):
        return [f"Port {node.port}: {'Serving ' + node.current_url if node.current_url else 'Idle'}" 
                for node in self.nodes]