import datetime


class MemoryCacheItem:
    def __init__(self, expires, value):
        self.expires = datetime.datetime.utcnow().timestamp() + expires
        self.value = value

    def is_expired(self):
        return datetime.datetime.utcnow().timestamp() > self.expires


class MemoryCache:
    def __init__(self):
        self.cache = {}

    def setex(self, key, expires, value):
        self.cache[key] = MemoryCacheItem(expires, value)

    def get(self, key):
        try:
            cache = self.cache[key]
            if cache.is_expired():
                return None
            return cache.value
        except KeyError:
            return None
