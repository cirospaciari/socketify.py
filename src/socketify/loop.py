import asyncio
import logging
from .tasks import create_task, TaskFactory
from .uv import UVLoop

import asyncio
import platform

is_pypy = platform.python_implementation() == "PyPy"

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
    def __init__(self, exception_handler=None, task_factory_max_items=0, idle_relaxation_time=0.01):

        # get the current running loop or create a new one without warnings
        self.loop = asyncio._get_running_loop()
        self._idle_count = 0
        self.is_idle = False
        self.idle_relaxation_time = idle_relaxation_time
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
        if is_pypy:  # PyPy async Optimizations
            if task_factory_max_items > 0:  # Only available in PyPy for now
                self._task_factory = TaskFactory(task_factory_max_items)
            else:
                self._task_factory = create_task
            self.run_async = self._run_async_pypy
            
            # TODO: check if any framework breaks without current_task(loop) support
            # custom task factory for other tasks
            def pypy_task_factory(loop, coro, context=None):
                return create_task(loop, coro, context=context)

            self.loop.set_task_factory(pypy_task_factory)
        else:
            
            # TODO: check if any framework breaks without current_task(loop) support
            # custom task factory for other tasks
            def cpython_task_factory(loop, coro, context=None):
                return create_task(loop, coro, context=context)

            self.loop.set_task_factory(cpython_task_factory)

            # CPython performs equals or worse using TaskFactory
            self.run_async = self._run_async_cpython

    def set_timeout(self, timeout, callback, user_data):
        return self.uv_loop.create_timer(timeout, 0, callback, user_data)

    def create_future(self):
        return self.loop.create_future()

    def _keep_alive(self):
        if self.started:
            relax = False
            if not self.is_idle:
                self._idle_count = 0
            elif self._idle_count < 10000:
                self._idle_count += 1
            else:
                relax = True
            
            self.is_idle = True
                
            if relax:
                self.uv_loop.run_nowait()

                if self._idle_count < 15000:
                    self._idle_count += 1
                    # we are idle not for long, wait 5s until next relax mode
                    self.loop.call_later(0.001, self._keep_alive)
                else:
                    # we are really idle now lets use less CPU
                    self.loop.call_later(self.idle_relaxation_time, self._keep_alive)
            else:
                self.uv_loop.run_nowait()
                # be more aggressive when needed
                self.loop.call_soon(self._keep_alive)
                
    def create_task(self, *args, **kwargs):
        # this is not using optimized create_task yet
        return self.loop.create_task(*args, **kwargs)

    def ensure_future(self, task):
        return asyncio.ensure_future(task, loop=self.loop)
    
    def set_event_loop(self, loop):
        needs_start = False
        if self.loop.is_running():
            self.stop()
        
        self.loop = loop
        if self.exception_handler is not None:
            self.loop.set_exception_handler(
                lambda loop, context: self.exception_handler(loop, context, None)
            )

        if is_pypy:  # PyPy async Optimizations
            # TODO: check if any framework breaks without current_task(loop) support
            # custom task factory for other tasks
            def pypy_task_factory(loop, coro, context=None):
                return create_task(loop, coro, context=context)

            self.loop.set_task_factory(pypy_task_factory)
        else:
            
            # TODO: check if any framework breaks without current_task(loop) support
            # custom task factory for other tasks
            def cpython_task_factory(loop, coro, context=None):
                return create_task(loop, coro, context=context)

            self.loop.set_task_factory(cpython_task_factory)
        if needs_start:
            self.run()

    def create_background_task(self, bg_task):
        def next_tick():
            self.ensure_future(bg_task())
        self.loop.call_soon(next_tick)

    def run_until_complete(self, task=None):
        self.started = True
        if task is not None:
            future = self.ensure_future(task)
        else:
            future = None
        self.loop.call_soon(self._keep_alive)
        self.loop.run_until_complete(future)
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
        # if loop._run_once is not available use loop.run_forever + loop.call_soon(loop.stop)
        # this is useful when using uvloop or custom loops
        try:
            self.loop._stopping = True
            self.loop._run_once()
        except Exception: 
            # this can be _StopError with means we should not call run_forever, but we can ignore it
            self.loop.call_soon(self.loop.stop)
            self.loop.run_forever()
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
        # this guarantees error 500 in case of uncaught exceptions, and can trigger the custom error handler
        # using an coroutine wrapper generates less overhead than using add_done_callback
        # this is an custom task/future with less overhead and that calls the first step
        future = self._task_factory(
            self.loop, task_wrapper(self.exception_handler, self.loop, response, task)
        )
        return None  # this future maybe already done and reused not safe to await

    def _run_async_cpython(self, task, response=None):
        # this guarantees error 500 in case of uncaught exceptions, and can trigger the custom error handler
        # using an coroutine wrapper generates less overhead than using add_done_callback
        # this is an custom task/future with less overhead and that calls the first step
        future = create_task(self.loop, task_wrapper(self.exception_handler, self.loop, response, task))
        return None  # this future is safe to await but we return None for compatibility, and in the future will be the same behavior as PyPy

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
