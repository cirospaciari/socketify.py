
import asyncio
import threading
import time

class Loop:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop_thread = None

    def start(self):
        self.loop_thread = threading.Thread(target=lambda loop: loop.run_forever(), args=(self.loop,), daemon=True)
        self.loop_thread.start()  
        
    def stop(self):
        #stop loop
        self.loop.call_soon_threadsafe(self.loop.stop) 
        #wait loop thread to stops
        self.loop_thread.join()
        # Find all running tasks in main thread:
        pending = asyncio.all_tasks(self.loop)
        # Run loop until tasks done
        self.loop.run_until_complete(asyncio.gather(*pending))

    def run_async(self, task):
        asyncio.run_coroutine_threadsafe(task, self.loop)
        return True
