import asyncio
import logging
from .tasks import create_task, create_task_with_factory
from .uv import UVLoop

import asyncio
import platform

is_pypy = platform.python_implementation() == 'PyPy'
async def task_wrapper(exception_handler, loop, response, task):
    try:
        return await task
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


class Loop:
    def __init__(self, exception_handler=None, task_factory_max_items=0):
        
        # get the current running loop or create a new one without warnings
        self.loop = asyncio._get_running_loop()
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
        self.uv_loop = UVLoop()

        if hasattr(exception_handler, "__call__"):
            self.exception_handler = exception_handler
            self.loop.set_exception_handler(
                lambda loop, context: exception_handler(loop, context, None)
            )
        else:
            self.exception_handler = None

        self.started = False
        if is_pypy: # PyPy async Optimizations
            if task_factory_max_items > 0: # Only available in PyPy for now
                self._task_factory = create_task_with_factory(task_factory_max_items)
            else:
                self._task_factory = create_task
            self.run_async = self._run_async_pypy
            # custom task factory
            def pypy_task_factory(loop, coro, context=None):
                return create_task(loop, coro, context=context)
            self.loop.set_task_factory(pypy_task_factory)
        else:
            # CPython performs worse using custom create_task, so native create_task is used
            # but this also did not allow the use of create_task_with_factory :/
            # native create_task do not allow to change context, callbacks, state etc
            
            self.run_async = self._run_async_cpython
        

    def set_timeout(self, timeout, callback, user_data):
        return self.uv_loop.create_timer(timeout, 0, callback, user_data)

    def create_future(self):
        return self.loop.create_future()

    def _keep_alive(self):
        if self.started:
            self.uv_loop.run_once()
            self.loop.call_soon(self._keep_alive)
   
    def create_task(self, *args, **kwargs):
        # this is not using optimized create_task yet
        return self.loop.create_task(*args, **kwargs)

    def ensure_future(self, task):
        return asyncio.ensure_future(task, loop=self.loop)

    def run_until_complete(self, task=None):
        self.started = True
        if task is not None:
            future = self.ensure_future(task)
        else:
            future = None    
        self.loop.call_soon(self._keep_alive)
        self.loop.run_until_complete()
        # clean up uvloop
        self.uv_loop.stop()
        return future

    def run(self, task=None):
        self.started = True
        if task is not None:
            future = self.ensure_future(task)
        else:
            future = None    
        self.loop.call_soon(self._keep_alive)
        self.loop.run_forever()
        # clean up uvloop
        self.uv_loop.stop()
        return future

    def run_once(self):
        # run one step of asyncio 
        self.loop._stopping = True
        self.loop._run_once()
        # run one step of libuv
        self.uv_loop.run_once()

        
    def stop(self):
        if self.started:
            # Just mark as started = False and wait
            self.started = False
            self.loop.stop()

    # Exposes native loop for uWS
    def get_native_loop(self):
        return self.uv_loop.get_native_loop()
   

    def _run_async_pypy(self, task, response=None):
        # this garanties error 500 in case of uncaught exceptions, and can trigger the custom error handler
        # using an coroutine wrapper generates less overhead than using add_done_callback 
        # this is an custom task/future with less overhead
        future = self._task_factory(self.loop, task_wrapper(self.exception_handler, self.loop, response, task))
        # force asyncio run once to enable req in async functions before first await
        self.loop._run_once()
        return None # this future maybe already done and reused not safe to await

    def _run_async_cpython(self, task, response=None):       
        # this garanties error 500 in case of uncaught exceptions, and can trigger the custom error handler
        # using an coroutine wrapper generates less overhead than using add_done_callback 
        future = self.loop.create_task(task_wrapper(self.exception_handler, self.loop, response, task))
        # force asyncio run once to enable req in async functions before first await
        self.loop._run_once()
        return None # this future is safe to await but we return None for compatibility, and in the future will be the same behavior as PyPy
    def dispose(self):
        if self.uv_loop:
            self.uv_loop.dispose()
            self.uv_loop = None

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
