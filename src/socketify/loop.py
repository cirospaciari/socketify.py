
import asyncio
import threading
import time

from .native import UVLoop


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
        self.uv_loop = UVLoop()
        if hasattr(exception_handler, '__call__'):
            self.exception_handler = exception_handler
            self.loop.set_exception_handler(lambda loop, context: exception_handler(loop, context, None))
        else:
            self.exception_handler = None

        asyncio.set_event_loop(self.loop)
        self.started = False
        self.last_defer = False

    def set_timeout(self, timeout, callback, user_data):
        return self.uv_loop.create_timer(timeout, 0, callback, user_data)

    def create_future(self):
        return self.loop.create_future()

    def start(self):
        self.started = True
        #start relaxed until first task
        self.timer = self.uv_loop.create_timer(0, 1, lambda loop: loop.run_once_asyncio(), self)

    def run(self):
        self.uv_loop.run()

    def run_once(self):
        self.uv_loop.run_once()

    def run_once_asyncio(self):
        #run only one step
        self.loop.call_soon(self.loop.stop)
        self.loop.run_forever()

    def stop(self):
        if(self.started):
            self.timer.stop()
            self.started = False
        #unbind run_once 
        #if is still running stops
        if self.loop.is_running(): 
            self.loop.stop()

        self.last_defer = None
        # Find all running tasks in main thread:
        pending = asyncio.all_tasks(self.loop)
        # Run loop until tasks done
        self.loop.run_until_complete(asyncio.gather(*pending))
        
    #Exposes native loop for uWS
    def get_native_loop(self):
        return self.uv_loop.get_native_loop()

    def run_async(self, task, response=None):
        #with run_once
        future = asyncio.ensure_future(task, loop=self.loop)

        #with threads
        future.add_done_callback(lambda f: future_handler(f, self.loop, self.exception_handler, response))

        #force asyncio run once to enable req in async functions before first await
        self.run_once_asyncio()

        # if response != None: #set auto cork
            # response.needs_cork = True
        return future



#  if sys.version_info >= (3, 11)
#         with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
#             runner.run(main())
#     else:
#         uvloop.install()
#         asyncio.run(main())