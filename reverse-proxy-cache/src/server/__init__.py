from .reverse_proxy import ReverseProxy
from .websocket_server import run_server

def start_websocket_server():
    run_server(ReverseProxy)
