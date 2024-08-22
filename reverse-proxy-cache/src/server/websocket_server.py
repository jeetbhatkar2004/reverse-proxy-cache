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

from src.server.reverse_proxy import ReverseProxy

clients = []

async def log_server(websocket, path):
    print("New client connected")
    clients.append(websocket)
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            data = json.loads(message)
            urls = data.get("urls", [])
            cache_strategy = data.get("cacheStrategy", "LRU")

            print(f"Cache strategy selected: {cache_strategy}")
            print(f"URLs to fetch: {urls}")

            # Select the cache strategy
            if cache_strategy == "LRU":
                cache = LRUCache(capacity=32)
            elif cache_strategy == "LFU":
                cache = LFUCache(capacity=32)
            elif cache_strategy == "FIFO":
                cache = FIFOCache(capacity=32)
            elif cache_strategy == "ARC":
                cache = ARCCache(capacity=32)
            elif cache_strategy == "RR":
                cache = RRCache(capacity=32)
            else:
                cache = LRUCache(capacity=32)  # Default to LRU if the strategy is unknown

            # Create the reverse proxy instance
            proxy = ReverseProxy(cache, urls)
            async with aiohttp.ClientSession() as session:
                proxy.session = session
                for url in urls:
                    print(f"Fetching URL: {url}")
                    result = await proxy.fetch(url)
                    
                    # Determine if it was a cache hit or miss
                    is_hit = result and "Cache hit" in result
                    response_message = f"Cache {'hit' if is_hit else 'miss'} for {url}"
                    
                    # Get cache stats
                    cache_stats = cache.get_cache_stats()
                    print(f"Current cache stats: {cache_stats}")  # Log the cache stats
                    
                    # Ensure that the response is always in JSON format
                    response_json = json.dumps({
                        "data": response_message,
                        "cacheStats": cache_stats
                    })

                    print(f"Sending response: {response_json}")
                    await websocket.send(response_json)
                    await asyncio.sleep(0.1)  # Simulate a delay for real-time effect
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        print("Client disconnected")
        clients.remove(websocket)

start_server = websockets.serve(log_server, "localhost", 6789)

async def main():
    print("Starting server...")
    await start_server

asyncio.get_event_loop().run_until_complete(main())
print("Server started")
asyncio.get_event_loop().run_forever()