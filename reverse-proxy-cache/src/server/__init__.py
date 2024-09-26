import asyncio
from .websocket_server import run_server

def start_websocket_server():
    asyncio.run(run_server())