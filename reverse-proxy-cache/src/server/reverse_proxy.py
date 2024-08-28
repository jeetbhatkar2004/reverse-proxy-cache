import asyncio
import aiohttp
from collections import deque
import time
import json

class Node:
    def __init__(self, port):
        self.port = port
        self.current_url = None

class ReverseProxy:
    def __init__(self, cache_class, urls, num_nodes, cache_size):
        self.cache = cache_class(capacity=cache_size)
        self.urls = asyncio.Queue()
        for url in urls:
            self.urls.put_nowait(url)
        self.nodes = [Node(8000 + i) for i in range(num_nodes)]
        self.url_locks = {url: asyncio.Lock() for url in urls}
        self.processed_urls = set()
        self.total_urls = len(urls)

    async def process_urls(self, websocket):
        async with aiohttp.ClientSession() as session:
            self.session = session
            tasks = [self.process_node(node, websocket) for node in self.nodes]
            await asyncio.gather(*tasks)

    async def process_node(self, node, websocket):
        while not self.urls.empty():
            url = await self.urls.get()
            node.current_url = url

            cache_status, content, port = await self.fetch(url, node)
            
            node.current_url = None
            self.processed_urls.add(url)

            cache_stats = self.cache.get_cache_stats()
            node_status = self.get_node_status()

            response_json = json.dumps({
                "data": f"{cache_status} for {url}",
                "cacheStats": cache_stats,
                "nodeStatus": node_status,
                "progress": f"{len(self.processed_urls)}/{self.total_urls}"
            })
            
            print(f"Sending response: {response_json}")
            await websocket.send(response_json)

            if len(self.processed_urls) >= self.total_urls:
                return

    async def fetch(self, url, node):
        async with self.url_locks[url]:
            if self.cache.contains(url):
                print(f"Cache hit for {url} on Node {node.port}")
                content = self.cache.get(url)
                return ("Cache hit", content, node.port)

            print(f"Cache miss for {url} on Node {node.port}")
            try:
                async with self.session.get(url, ssl=False, timeout=10) as response:
                    content = await response.text()
                    self.cache.put(url, content)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"Failed to fetch {url} on Node {node.port}: {e}")
                return (f"Error fetching {url}", None, node.port)

            return (f"Cache miss (Node {node.port})", content, node.port)

    def get_node_status(self):
        return [f"Port {node.port}: {'Serving ' + node.current_url if node.current_url else 'Idle'}" 
                for node in self.nodes]