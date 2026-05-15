import sys
import time
import requests
import threading
from collections import deque

lock = threading.Lock()
cache = {}
order = deque()
cache_size = 0

def init_cache(size):
    # TODO: initialize any global data structures as needed
    global cache, order, cache_size
    cache = {}
    order = deque()
    cache_size = size

def http_get(url, http_session):
    """Fetch url with retries (up to 5 seconds total wait). Returns (content_bytes, hit)."""
    with lock:
        if url in cache:
            return cache[url], True

    wait = 0.1
    total_waited = 0
    while True:
        try:
            resp = http_session.get(url)
            break
        except requests.exceptions.ConnectionError:
            total_waited += wait
            if total_waited > 5:
                raise
            print(f"RETRY {url} after {wait}s (total waited: {total_waited}s)")
            time.sleep(wait)

    if resp.status_code == 404:
        content = None
    else:
        resp.raise_for_status()
        content = resp.content

    with lock:
        if url not in cache:
            if len(cache) >= cache_size:
               first_in = order.popleft()
               cache.pop(first_in)
            cache[url] = content
            order.append(url)

    return content, False

if __name__ == "__main__":
    init_cache(3)
    session = requests.Session()
    hits = 0
    for url in sys.argv[1:]:
        _, hit = http_get(url, session)
        if hit:
            hits += 1
    print(f"hits: {hits}")
