import asyncio
import json
import websockets
import sys
import os
import socket
from flask import Flask, send_file
from threading import Thread
from flask_cors import CORS

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

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

async def handle_client(websocket, path):
    print("New client connected")
    try:
        while True:
            message = await websocket.recv()
            await process_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Error occurred: {e}")

async def process_message(websocket, message):
    print(f"Received message: {message}")
    data = json.loads(message)
    urls = data.get("urls", [])
    cache_strategy = data.get("cacheStrategy", "LRU")
    load_balancer = data.get("loadBalancer", "round_robin")
    num_nodes = data.get("numNodes", 1)
    cache_size = data.get("cacheSize", 1)

    print(f"Cache strategy selected: {cache_strategy}")
    print(f"Load balancer selected: {load_balancer}")
    print(f"Number of nodes: {num_nodes}")
    print(f"Cache size: {cache_size}")
    print(f"URLs to fetch: {urls}")

    cache_class = get_cache_strategy(cache_strategy)
    redis_db_number = 2
    cache_instance = cache_class(capacity=cache_size, redis_db=redis_db_number)

    cache_instance.clear()

    proxy_ip = get_local_ip()
    proxy = ReverseProxy(cache_instance, urls, num_nodes, cache_size, load_balancer, proxy_ip)
    
    # Send initial proxy IP information
    await websocket.send(json.dumps({"proxyIP": proxy_ip}))

    await proxy.process_urls(websocket)

    await websocket.send(json.dumps({"data": "All URLs processed", "final": True, "proxyIP": proxy_ip}))
    print("All URLs processed. Ready for next request.")
    proxy.save_cache_to_csv()

async def start_websocket_server():
    server = await websockets.serve(handle_client, "localhost", 6789)
    print("WebSocket server started on ws://localhost:6789")
    await server.wait_closed()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/get_cached_content')
def get_cached_content():
    file_path = os.path.join(os.path.dirname(__file__), '/Users/jeetbhatkar/Documents/Code/reverse-proxy-cache/reverse-proxy-cache/src/cached_content.csv')
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='text/csv')
    else:
        return "Cached content file not found", 404

def run_flask_app():
    app.run(debug=False, use_reloader=False, port=5001)

async def run_server():
    flask_thread = Thread(target=run_flask_app)
    flask_thread.start()
    print("Flask server started on port 5001")

    await start_websocket_server()

if __name__ == "__main__":
    asyncio.run(run_server())