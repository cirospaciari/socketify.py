import asyncio
import logging
import threading
from .uv import UVLoop

import asyncio

def future_handler(future, loop, exception_handler, response):
    try:
        future.result()
        return None
    except Exception as error:
        if hasattr(exception_handler, "__call__"):
            exception_handler(loop, error, response)
        else:
            try:
                # just log in console the error to call attention
                logging.error("Uncaught Exception: %s" % str(error))
                if response != None:
                    response.write_status(500).end("Internal Error")
            finally:
                return None
        return None


class Loop:
    def __init__(self, exception_handler=None):
        self.loop = asyncio.new_event_loop()
        self.uv_loop = UVLoop()

        if hasattr(exception_handler, "__call__"):
            self.exception_handler = exception_handler
            self.loop.set_exception_handler(
                lambda loop, context: exception_handler(loop, context, None)
            )
        else:
            self.exception_handler = None

        asyncio.set_event_loop(self.loop)
        self.started = False
        self.last_defer = False

    def set_timeout(self, timeout, callback, user_data):
        return self.uv_loop.create_timer(timeout, 0, callback, user_data)

    def create_future(self):
        return self.loop.create_future()

    def keep_alive(self):
        if self.started:
            self.uv_loop.run_once()
            self.loop.call_soon(self.keep_alive)
   
    def run(self):
        self.started = True
        self.loop.call_soon(self.keep_alive)
        self.loop.run_forever()
        # clean up uvloop
        self.uv_loop.stop()

    def run_once(self):
        # run one step of asyncio 
        self.loop._stopping = True
        self.loop._run_once()
        # run one step of libuv
        self.uv_loop.run_once()

        
    def stop(self):
        # Just mark as started = False and wait
        self.started = False
        self.loop.stop()

    # Exposes native loop for uWS
    def get_native_loop(self):
        return self.uv_loop.get_native_loop()

    def run_async(self, task, response=None):
        # with run_once
        future = asyncio.ensure_future(task, loop=self.loop)

        # with threads
        future.add_done_callback(
            lambda f: future_handler(f, self.loop, self.exception_handler, response)
        )
        # force asyncio run once to enable req in async functions before first await
        self.loop._run_once()

        return future


#  if sys.version_info >= (3, 11)
#         with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
#             runner.run(main())
#     else:
#         uvloop.install()
#         asyncio.run(main())


# see ./native/uv_selector.txt
# will only work on linux and macos
# class UVSelector(asyncio.SelectorEventLoop):
#     def register(self, fileobj, events, data=None):
#         fd = fileobj.fileno()
#         if fd == -1:
#             return None
#         mask = int(events)
#         selector_key = (fs, mask, data)
#         pass

#     def tick(self):
#         pass

# # We expose our own event loop for use with asyncio
# class AsyncioUVLoop(asyncio.SelectorEventLoop):
# 	def __init__(self):
# 		self.selector = UVSelector()
# 		super().__init__(self.selector)
# 	def call_soon(self, *args, **kwargs):
# 		self.selector.tick()
# 		return super().call_soon(*args, **kwargs)
# 	def call_at(self, *args, **kwargs):
# 		self.selector.tick()
# 		return super().call_at(*args, **kwargs)

# asyncio.set_event_loop(uws.Loop())
# asyncio.get_event_loop().run_forever()
