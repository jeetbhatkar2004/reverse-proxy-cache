import asyncio
import aiohttp
import json
import csv
import logging
from typing import List, Dict, Any
from scapy.all import sniff, IP
from collections import defaultdict
import threading
from .load_balancers import (
    RoundRobinLoadBalancer,
    LeastConnectionsLoadBalancer,
    RandomLoadBalancer,
    WeightedRoundRobinLoadBalancer,
    IPHashLoadBalancer
)

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='reverse_proxy.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Node:
    def __init__(self, port: int):
        self.port = port
        self.current_url: str = None
        self.active_connections: int = 0

class ReverseProxy:
    def __init__(self, cache_instance: Any, urls: List[str], num_nodes: int, cache_size: int, 
                 load_balancer_type: str = "round_robin", proxy_ip: str = None):
        self.cache = cache_instance
        self.urls = asyncio.Queue()
        for url in urls:
            self.urls.put_nowait(url)
        self.nodes = [Node(8000 + i) for i in range(num_nodes)]
        self.url_locks = {url: asyncio.Lock() for url in urls}
        self.processed_urls: set = set()
        self.total_urls = len(urls)
        self.proxy_ip = proxy_ip or '127.0.0.1'
        self.session: aiohttp.ClientSession = None
        self.load_balancer = self.initialize_load_balancer(load_balancer_type, num_nodes)
        
        # Network tracing attributes
        self.packet_counts = defaultdict(int)
        self.trace_lock = threading.Lock()
        self.trace_thread = threading.Thread(target=self._start_trace)
        self.trace_thread.daemon = True
        self.trace_thread.start()

        logger.info(f"ReverseProxy initialized with proxy IP: {self.proxy_ip}")

    def initialize_load_balancer(self, load_balancer_type: str, num_nodes: int) -> Any:
        if load_balancer_type == "least_connections":
            return LeastConnectionsLoadBalancer(self.nodes)
        elif load_balancer_type == "random":
            return RandomLoadBalancer(self.nodes)
        elif load_balancer_type == "weighted_round_robin":
            weights = [1] * num_nodes  # You can adjust these weights as needed
            return WeightedRoundRobinLoadBalancer(self.nodes, weights)
        elif load_balancer_type == "ip_hash":
            return IPHashLoadBalancer(self.nodes)
        else:
            logger.warning(f"Unknown or default load balancer type: {load_balancer_type}. Using Round Robin.")
            return RoundRobinLoadBalancer(self.nodes)

    def _start_trace(self):
        logger.info(f"Starting network trace for proxy IP: {self.proxy_ip}")
        sniff(filter=f"host {self.proxy_ip}", prn=self._packet_callback, store=0)

    def _packet_callback(self, packet):
        if IP in packet:
            with self.trace_lock:
                if packet[IP].src == self.proxy_ip:
                    self.packet_counts['sent'] += 1
                elif packet[IP].dst == self.proxy_ip:
                    self.packet_counts['received'] += 1
            logger.debug(f"Packet processed: src={packet[IP].src}, dst={packet[IP].dst}")

    async def process_urls(self, websocket: Any) -> None:
        async with aiohttp.ClientSession() as session:
            self.session = session
            tasks = [self._process_node(websocket) for _ in range(len(self.nodes))]
            await asyncio.gather(*tasks)
        
        # After processing all URLs, send the network trace report
        await self._send_trace_report(websocket)

    async def _process_node(self, websocket: Any) -> None:
        while not self.urls.empty():
            url = await self.urls.get()
            node = self.load_balancer.get_next_node(url if isinstance(self.load_balancer, IPHashLoadBalancer) else None)
            node.active_connections += 1
            node.current_url = url

            try:
                cache_status, content = await self._fetch(url, node)
                await self._send_response(websocket, url, cache_status, content)
            finally:
                node.active_connections -= 1
                node.current_url = None

            self.processed_urls.add(url)

            if len(self.processed_urls) >= self.total_urls:
                return

    async def _fetch(self, url: str, node: Node) -> tuple[str, str]:
        async with self.url_locks[url]:
            content = self.cache.get(url)
            if content != -1:
                logger.info(f"Cache hit for {url} on Node {node.port}")
                return "Cache hit", content
            
            logger.info(f"Cache miss for {url} on Node {node.port}")
            try:
                async with self.session.get(url, ssl=False, timeout=3) as response:
                    content = await response.text()
                    self.cache.put(url, content)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(f"Failed to fetch {url} on Node {node.port}: {e}")
                return f"Error fetching {url}", None

            return f"Cache miss (Node {node.port})", content

    async def _send_response(self, websocket: Any, url: str, cache_status: str, content: str) -> None:
        response_json = json.dumps({
            "data": f"{cache_status} for {url}",
            "cacheStats": self.cache.get_cache_stats(),
            "nodeStatus": self._get_node_status(),
            "progress": f"{len(self.processed_urls)}/{self.total_urls}",
            "loadBalancer": self.load_balancer.__class__.__name__,
            "proxyIP": self.proxy_ip,
            "responseIP": self.proxy_ip,
            "url": url,
            "content": content
        })
        
        logger.debug(f"Sending response: {response_json}")
        await websocket.send(response_json)

    async def _send_trace_report(self, websocket: Any) -> None:
        with self.trace_lock:
            report = {
                "traceReport": {
                    "packetsSent": self.packet_counts['sent'],
                    "packetsReceived": self.packet_counts['received'],
                    "proxyIP": self.proxy_ip
                }
            }
        logger.info(f"Sending trace report: {report}")
        await websocket.send(json.dumps(report))

    def _get_node_status(self) -> List[str]:
        return [f"Port {node.port}: {'Serving ' + node.current_url if node.current_url else 'Idle'} (Active: {node.active_connections})" 
                for node in self.nodes]
        
    def save_cache_to_csv(self, filename: str = 'cached_content.csv') -> None:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['url', 'content']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for url, content in self.cache.items():
                writer.writerow({'url': url, 'content': content})
        logger.info(f"Cached content saved to {filename}")

    def get_proxy_ip(self) -> str:
        return self.proxy_ip