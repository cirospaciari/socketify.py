
import asyncio
import threading
import time

def loop_thread(loop, exception_handler):
    if hasattr(exception_handler, '__call__'):
        loop.set_exception_handler(lambda loop, context: exception_handler(loop, context, None))
    loop.run_forever()

def future_handler(future, loop, exception_handler, response):
    try:
        future.result()
        return None
    except Exception as error:
        if hasattr(exception_handler, '__call__'):
            exception_handler(loop, error, response)
        else:
            try:
                 #just log in console the error to call attention
                print("Uncaught Exception: %s" % str(error))
                if response != None:
                    response.write_status(500).end("Internal Error")
            finally:
                return

class Loop:
    def __init__(self, exception_handler=None):
        self.loop = asyncio.new_event_loop()
        if hasattr(exception_handler, '__call__'):
            self.exception_handler = exception_handler
            self.loop.set_exception_handler(lambda loop, context: exception_handler(loop, context, None))
        else:
            self.exception_handler = None

        asyncio.set_event_loop(self.loop)
        self.loop_thread = None

    def start(self):
        self.loop_thread = threading.Thread(target=loop_thread, args=(self.loop,self.exception_handler), daemon=True)
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

    def run_async(self, task, response=None):
        future = asyncio.run_coroutine_threadsafe(task, self.loop)
        future.add_done_callback(lambda f: future_handler(f, self.loop, self.exception_handler, response))
        return future
