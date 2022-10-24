import asyncio
from .memory_cache import MemoryCache

# 2 LEVEL CACHE (Redis to share amoung worker, Memory to be much faster)
class TwoLevelCache:
    def __init__(self, redis_conection, memory_expiration_time=3, redis_expiration_time=10):
        self.memory_cache = MemoryCache()
        self.redis_conection = redis_conection
        self.memory_expiration_time = memory_expiration_time
        self.redis_expiration_time = redis_expiration_time

    #set cache to redis and memory
    def set(self, key, data):
        try:
            #never cache invalid data
            if data == None:
                return False
            self.redis_conection.setex(key, self.redis_expiration_time, data)
            self.memory_cache.setex(key, self.memory_expiration_time, data)
            return True
        except Exception as err:
            print(err)
            return False
                
    def get(self, key):
        try:
            value = self.memory_cache.get(key)
            if value != None:
                return value
            #no memory cache so, got to redis
            value = self.redis_conection.get(key)
            if value != None:
                #refresh memory cache to speed up
                self.memory_cache.setex(key, self.memory_expiration_time, data)
            return value
        except Exception as err:
            return None

    #if more than 1 worker/request try to do this request, only one will call the Model and the others will get from cache
    async def run_once(self, key, timeout, executor, *args):
        result = None
        try:
            lock = self.redis_conection.lock(f"lock-{key}", blocking_timeout=timeout)
            #wait lock (some request is yeat not finish)
            while lock.locked():
                await asyncio.sleep(0)
            try:
                lock.acquire(blocking=False)
                #always check cache first
                cached = self.get(key)
                if cached != None:
                    return cached
                result = await executor(*args)
                if result != None:
                    self.set(key, result)
            except Exception as err:
                # the lock wasn't acquired
                pass
            finally:
                lock.release()
        except Exception as err:
            #cannot even create or release the lock
            pass
        finally:
            #if result is None, try cache one last time
            if result == None:
                cache = self.get(key)
                if cache != None:
                    return cache
            return result