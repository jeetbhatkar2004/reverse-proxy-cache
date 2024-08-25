import asyncio
import json
import websockets
import sys
import os

# Add the project's root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.cache.lru_cache import LRUCache
from src.cache.lfu_cache import LFUCache
from src.cache.fifo_cache import FIFOCache
from src.cache.arc_cache import ARCCache
from src.cache.rr_cache import RRCache
from src.server.reverse_proxy import ReverseProxy

def get_cache_strategy(strategy_name):
    cache_strategies = {
        "LRU": LRUCache,
        "LFU": LFUCache,
        "FIFO": FIFOCache,
        "ARC": ARCCache,
        "RR": RRCache
    }
    return cache_strategies.get(strategy_name, LRUCache)

async def handle_client(websocket, path, stop_server_event):
    print("New client connected")
    try:
        message = await websocket.recv()
        await process_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        stop_server_event.set()

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

    processed_count = 0
    total_urls = len(urls)

    async for result in proxy.process_urls():
        cache_status, content, node_port = result
        cache_stats = proxy.cache.get_cache_stats()
        node_status = proxy.get_node_status()
        
        processed_count += 1
        response_json = json.dumps({
            "data": f"{cache_status} for {proxy.nodes[node_port - 8000].current_url}",
            "cacheStats": cache_stats,
            "nodeStatus": node_status,
            "progress": f"{processed_count}/{total_urls}"
        })

        print(f"Sending response: {response_json}")
        await websocket.send(response_json)

    # Send a final message to indicate all URLs have been processed
    await websocket.send(json.dumps({"data": "All URLs processed", "final": True}))
    print("All URLs processed. Closing connection.")

async def start_server(stop_server_event):
    server = await websockets.serve(
        lambda ws, path: handle_client(ws, path, stop_server_event),
        "localhost", 6789
    )
    print("Server started")
    await stop_server_event.wait()
    server.close()
    await server.wait_closed()
    print("Server stopped")

async def run_server():
    stop_server_event = asyncio.Event()
    server_task = asyncio.create_task(start_server(stop_server_event))
    await server_task

if __name__ == "__main__":
    asyncio.run(run_server())