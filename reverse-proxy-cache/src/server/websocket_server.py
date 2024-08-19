import asyncio
import json
import websockets

clients = []

async def log_server(websocket, path):
    clients.append(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received data: {data}")
    finally:
        clients.remove(websocket)

async def notify_clients(message):
    if clients:
        await asyncio.wait([client.send(message) for client in clients])

start_server = websockets.serve(log_server, "localhost", 6789)

async def main():
    await start_server

asyncio.get_event_loop().run_until_complete(main())
asyncio.get_event_loop().run_forever()