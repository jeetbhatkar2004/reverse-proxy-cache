import asyncio
import ssl
from aiohttp import web

async def handle_request(request):
    return web.Response(text="Hello, Mutual TLS World!")

# SSL Context Setup for mTLS
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile='server-cert.pem', keyfile='server-key.pem')
ssl_context.load_verify_locations(cafile='client-cert.pem')
ssl_context.verify_mode = ssl.CERT_REQUIRED  # Require a client certificate

app = web.Application()
app.router.add_get('/', handle_request)

# Run the server with SSL/TLS on localhost with mutual authentication
web.run_app(app, port=8443, ssl_context=ssl_context)
