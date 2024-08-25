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
from .reverse_proxy import ReverseProxy  # Ensure this import matches your file structure

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

async def handle_client(websocket, path):
    print("New client connected")
    clients.add(websocket)
    try:
        async for message in websocket:
            await process_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        clients.remove(websocket)

async def process_message(websocket, message):
    print(f"Received message: {message}")
    data = json.loads(message)
    urls = data.get("urls", [])
    cache_strategy = data.get("cacheStrategy", "LRU")
    num_nodes = data.get("numNodes", 1)

    print(f"Cache strategy selected: {cache_strategy}")
    print(f"Number of nodes: {num_nodes}")
    print(f"URLs to fetch: {urls}")

    cache_class = get_cache_strategy(cache_strategy)
    cache = cache_class(capacity=32)
    proxy = ReverseProxy(cache, urls, num_nodes)

    results = await proxy.fetch_all()

    for result in results:
        cache_status, content, node_port = result
        cache_stats = proxy.cache.get_cache_stats()
        node_status = proxy.get_node_status()
        
        response_json = json.dumps({
            "data": f"{cache_status} for {urls[results.index(result)]}",
            "cacheStats": cache_stats,
            "nodeStatus": node_status
        })

        print(f"Sending response: {response_json}")
        await websocket.send(response_json)
        await asyncio.sleep(0.1)  # Small delay between messages

    # Send a final message to indicate all URLs have been processed
    await websocket.send(json.dumps({"data": "All URLs processed", "final": True}))

async def start_server():
    server = await websockets.serve(handle_client, "localhost", 6789)
    print("Server started")
    await server.wait_closed()

def run_server():
    asyncio.run(start_server())

if __name__ == "__main__":
    run_server()