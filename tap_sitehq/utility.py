import os
import time
import asyncio
import singer.metrics as metrics
from datetime import datetime


# constants
base_url = "https://stormy-sands-87474.herokuapp.com/"

# Rate-limited to 10 requests per 10 seconds per https://sitehq-docs.netlify.app/
class RateLimiter:
    rate = 10  # requests per second

    def __init__(self, client):
        self.client = client
        self.tokens = self.rate
        self.updated_at = time.monotonic()

    async def get(self, *args, **kwargs):
        await self.wait_for_token()
        return self.client.get(*args, **kwargs)

    async def wait_for_token(self):
        while self.tokens < 1:
            self.add_new_tokens()
            await asyncio.sleep(0.1)
        self.tokens -= 1

    # would be nice to just make this an async loop but you can't do that easily in Python, unlike Node
    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.rate
        if self.tokens + new_tokens >= 1:
            self.tokens = min(self.tokens + new_tokens, self.rate)
            self.updated_at = now


async def get_generic(session, source, url, qs={}):
    with metrics.http_request_timer(source) as timer:
        url = base_url + url + build_query_string(qs)
        async with await session.get(url) as resp:
            timer.tags[metrics.Tag.http_status_code] = resp.status
            resp.raise_for_status()
            return (await resp.json())["data"]


def formatDate(dt):
    return datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def build_query_string(dict):
    if len(dict) == 0:
        return ""

    return "?" + "&".join(["{}={}".format(k, v) for k, v in dict.items()])
