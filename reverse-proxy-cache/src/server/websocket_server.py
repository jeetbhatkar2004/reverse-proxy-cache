import asyncio
import json
import websockets
import sys
import os
import aiohttp

# Add the project's root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.cache.lru_cache import LRUCache
from src.cache.lfu_cache import LFUCache
from src.cache.fifo_cache import FIFOCache
from src.cache.arc_cache import ARCCache
from src.cache.rr_cache import RRCache

clients = set()

def get_cache_strategy(strategy_name):
    cache_strategies = {
        "LRU": LRUCache,
        "LFU": LFUCache,
        "FIFO": FIFOCache,
        "ARC": ARCCache,
        "RR": RRCache
    }
    return cache_strategies.get(strategy_name, LRUCache)

async def handle_client(websocket, path, ReverseProxy):
    print("New client connected")
    clients.add(websocket)
    try:
        async for message in websocket:
            await process_message(websocket, message, ReverseProxy)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        clients.remove(websocket)

async def process_message(websocket, message, ReverseProxy):
    print(f"Received message: {message}")
    data = json.loads(message)
    urls = data.get("urls", [])
    cache_strategy = data.get("cacheStrategy", "LRU")

    print(f"Cache strategy selected: {cache_strategy}")
    print(f"URLs to fetch: {urls}")

    cache_class = get_cache_strategy(cache_strategy)
    cache = cache_class(capacity=32)
    proxy = ReverseProxy(cache, urls)

    async with aiohttp.ClientSession() as session:
        proxy.session = session
        for url in urls:
            await process_url(websocket, proxy, url)

async def process_url(websocket, proxy, url):
    print(f"Fetching URL: {url}")
    result = await proxy.fetch(url)
    
    if result is None:
        response_message = f"Failed to fetch {url}"
    else:
        # The fetch method now returns a tuple (cache_status, content)
        cache_status, content = result
        response_message = f"{cache_status} for {url}"
    
    cache_stats = proxy.cache.get_cache_stats()
    print(f"Current cache stats: {cache_stats}")
    
    response_json = json.dumps({
        "data": response_message,
        "cacheStats": cache_stats
    })

    print(f"Sending response: {response_json}")
    await websocket.send(response_json)
    await asyncio.sleep(0.1)  # Simulate a delay for real-time effect

async def start_server(ReverseProxy):
    server = await websockets.serve(
        lambda ws, path: handle_client(ws, path, ReverseProxy),
        "localhost", 6789
    )
    print("Server started")
    await server.wait_closed()

def run_server(ReverseProxy):
    asyncio.run(start_server(ReverseProxy))