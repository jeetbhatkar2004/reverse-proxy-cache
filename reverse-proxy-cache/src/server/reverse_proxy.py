import asyncio
import aiohttp
import time
import csv
import json
import socket
from .load_balancers import (
    RoundRobinLoadBalancer,
    LeastConnectionsLoadBalancer,
    RandomLoadBalancer,
    WeightedRoundRobinLoadBalancer,
    IPHashLoadBalancer
)

class Node:
    def __init__(self, port):
        self.port = port
        self.current_url = None
        self.active_connections = 0

class ReverseProxy:
    def __init__(self, cache_instance, urls, num_nodes, cache_size, load_balancer_type="round_robin", proxy_ip=None):
        self.cache = cache_instance
        self.urls = asyncio.Queue()
        for url in urls:
            self.urls.put_nowait(url)
        self.nodes = [Node(8000 + i) for i in range(num_nodes)]
        self.url_locks = {url: asyncio.Lock() for url in urls}
        self.processed_urls = set()
        self.total_urls = len(urls)
        self.load_balancer_type = load_balancer_type
        self.proxy_ip = proxy_ip or '127.0.0.1'
        
        self.load_balancer = self.initialize_load_balancer(load_balancer_type, num_nodes)

    def get_local_ip(self):
        return self.proxy_ip

    def initialize_load_balancer(self, load_balancer_type, num_nodes):
        if load_balancer_type == "round_robin":
            return RoundRobinLoadBalancer(self.nodes)
        elif load_balancer_type == "least_connections":
            return LeastConnectionsLoadBalancer(self.nodes)
        elif load_balancer_type == "random":
            return RandomLoadBalancer(self.nodes)
        elif load_balancer_type == "weighted_round_robin":
            weights = [1] * num_nodes  # You can adjust these weights as needed
            return WeightedRoundRobinLoadBalancer(self.nodes, weights)
        elif load_balancer_type == "ip_hash":
            return IPHashLoadBalancer(self.nodes)
        else:
            print(f"Unknown load balancer type: {load_balancer_type}. Using Round Robin.")
            return RoundRobinLoadBalancer(self.nodes)

    async def process_urls(self, websocket):
        async with aiohttp.ClientSession() as session:
            self.session = session
            tasks = [self.process_node(websocket) for _ in range(len(self.nodes))]
            await asyncio.gather(*tasks)

    async def process_node(self, websocket):
        while not self.urls.empty():
            url = await self.urls.get()
            if self.load_balancer_type == "ip_hash":
                node = self.load_balancer.get_next_node(url)  # Pass URL as IP for IP hash
            else:
                node = self.load_balancer.get_next_node()
            node.active_connections += 1
            node.current_url = url

            try:
                cache_status, content, port, response_ip = await self.fetch(url, node)
            finally:
                node.active_connections -= 1
                node.current_url = None

            self.processed_urls.add(url)

            await self.send_response(websocket, url, cache_status, response_ip)

            if len(self.processed_urls) >= self.total_urls:
                return


    async def fetch(self, url, node):
        async with self.url_locks[url]:
            content = self.cache.get(url)
            if content != -1:
                print(f"Cache hit for {url} on Node {node.port}")
                return ("Cache hit", content, node.port, self.proxy_ip)
            else:
                print(f"Cache miss for {url} on Node {node.port}")
                try:
                    async with self.session.get(url, ssl=False, timeout=3) as response:
                        content = await response.text()
                        self.cache.put(url, content)
                        response_ip = response.url.host
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    print(f"Failed to fetch {url} on Node {node.port}: {e}")
                    return (f"Error fetching {url}", None, node.port, None)

                return (f"Cache miss (Node {node.port})", content, node.port, response_ip)
    async def send_response(self, websocket, url, cache_status, response_ip):
        cache_stats = self.cache.get_cache_stats()
        node_status = self.get_node_status()

        response_json = json.dumps({
            "data": f"{cache_status} for {url}",
            "cacheStats": cache_stats,
            "nodeStatus": node_status,
            "progress": f"{len(self.processed_urls)}/{self.total_urls}",
            "loadBalancer": self.load_balancer_type,
            "proxyIP": self.proxy_ip,
            "responseIP": response_ip or "N/A",
            "url": url
        })
        
        print(f"Sending response: {response_json}")
        await websocket.send(response_json)

    def get_node_status(self):
        return [f"Port {node.port}: {'Serving ' + node.current_url if node.current_url else 'Idle'} (Active: {node.active_connections})" 
                for node in self.nodes]
        
    def save_cache_to_csv(self, filename='cached_content.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['url', 'content']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for url, content in self.cache.items():
                writer.writerow({'url': url, 'content': content})
        print(f"Cached content saved to {filename}")

    def get_proxy_ip(self):
        return self.proxy_ip