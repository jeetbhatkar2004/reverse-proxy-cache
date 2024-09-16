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
    load_balancer = data.get("loadBalancer", "round_robin")
    num_nodes = data.get("numNodes", 1)
    cache_size = data.get("cacheSize", 1)  # Default to 1 if not provided

    print(f"Cache strategy selected: {cache_strategy}")
    print(f"Load balancer selected: {load_balancer}")
    print(f"Number of nodes: {num_nodes}")
    print(f"Cache size: {cache_size}")
    print(f"URLs to fetch: {urls}")

    cache_class = get_cache_strategy(cache_strategy)
    redis_db_number = 2  # Use a separate Redis database for the cache
    cache_instance = cache_class(capacity=cache_size, redis_db=redis_db_number)

    # Clear the cache at the start of processing
    cache_instance.clear()

    proxy = ReverseProxy(cache_instance, urls, num_nodes, cache_size, load_balancer)
    await proxy.process_urls(websocket)

    # Send a final message to indicate all URLs have been processed
    await websocket.send(json.dumps({"data": "All URLs processed", "final": True}))
    print("All URLs processed. Closing connection.")
    proxy.save_cache_to_csv()



async def start_server(stop_server_event):
    server = await websockets.serve(
        lambda ws, path: handle_client(ws, path, stop_server_event),
        "localhost", 6789
    )
    print("Server started")
    await stop_server_event.wait()
    await server.wait_closed()
    print("Server stopped")

async def run_server():
    stop_server_event = asyncio.Event()
    server_task = asyncio.create_task(start_server(stop_server_event))
    await server_task

if __name__ == "__main__":
    asyncio.run(run_server())
