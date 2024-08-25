import asyncio
import aiohttp
from collections import deque

class Node:
    def __init__(self, port):
        self.port = port
        self.current_url = None

class LoadBalancer:
    def __init__(self, num_nodes):
        self.nodes = [Node(8000 + i) for i in range(num_nodes)]
        self.node_queue = asyncio.Queue()
        for node in self.nodes:
            self.node_queue.put_nowait(node)

    async def get_next_available_node(self):
        return await self.node_queue.get()

    def release_node(self, node):
        node.current_url = None
        self.node_queue.put_nowait(node)

class ReverseProxy:
    def __init__(self, cache, urls, num_nodes):
        self.cache = cache
        self.urls = urls
        self.session = None
        self.load_balancer = LoadBalancer(num_nodes)
        self.lock = asyncio.Lock()

    async def fetch_all(self):
        async with aiohttp.ClientSession() as self.session:
            tasks = [self.fetch(url) for url in self.urls]
            results = await asyncio.gather(*tasks)
        return results

    async def fetch(self, url):
        node = await self.load_balancer.get_next_available_node()
        try:
            node.current_url = url
            async with self.lock:
                if self.cache.contains(url):
                    print(f"Cache hit for {url}")
                    return ("Cache hit", self.cache.get(url), node.port)

            print(f"Cache miss for {url}")
            try:
                async with self.session.get(url, ssl=False, timeout=10) as response:
                    await asyncio.sleep(1.5)  # Simulate processing time
                    content = await response.text()
                    async with self.lock:
                        self.cache.put(url, content)
                    return (f"Cache miss (Node {node.port})", content, node.port)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"Failed to fetch {url}: {e}")
                return (f"Error fetching {url}", None, node.port)
        finally:
            self.load_balancer.release_node(node)

    def get_node_status(self):
        return [f"Port {node.port}: {'Serving ' + node.current_url if node.current_url else 'Idle'}" 
                for node in self.load_balancer.nodes]