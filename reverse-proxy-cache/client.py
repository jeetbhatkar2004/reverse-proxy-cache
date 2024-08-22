import aiohttp
import asyncio
import ssl

async def fetch():
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_cert_chain(certfile='client-cert.pem', keyfile='client-key.pem')
    ssl_context.load_verify_locations(cafile='server-cert.pem')

    async with aiohttp.ClientSession() as session:
        async with session.get('https://localhost:8443', ssl=ssl_context) as response:
            print(await response.text())

asyncio.run(fetch())
