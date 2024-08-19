import asyncio
import aiohttp


class ReverseProxy:
    def __init__(self, cache, urls):
        self.cache = cache
        self.urls = urls
        self.session = None
        self.lock = asyncio.Lock()

    async def fetch(self, url):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self.lock:
                    if self.cache.contains(url):
                        print(f"Cache hit for {url}")
                        return self.cache.get(url)
                    print(f"Cache miss for {url}")

                async with self.session.get(url, ssl=False, timeout=10) as response:
                    content = await response.text()
                    
                    async with self.lock:
                        self.cache.put(url, content)
                    
                    return content
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    print(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                    return None
                await asyncio.sleep(1)  # Wait before retrying