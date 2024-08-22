import asyncio
import aiohttp
from aiohttp import web

async def handle_request(request):
    # Replace https://localhost:8443 with the correct backend URL and port
    url = str(request.url).replace('https://localhost:8443', 'http://localhost:8080')  # Adjust the port and protocol
    print(f"Forwarding request to: {url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.text()
                return web.Response(text=data)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return web.Response(text=f"An error occurred: {str(e)}", status=500)


# aiohttp Application Setup
app = web.Application()
app.router.add_route('*', '/{tail:.*}', handle_request)

# Run the server without SSL on localhost for testing
web.run_app(app, port=8443)
