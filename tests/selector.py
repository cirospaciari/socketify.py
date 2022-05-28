from libuv import lib, ffi
import signal
import asyncio
import selectors
# loop = lib.uv_default_loop()
# print(loop)
# lib.uv_run(loop, lib.UV_RUN_ONCE)
        

@ffi.callback("void(uv_timer_t*)")
def selector_timer_handler(timer):
    global selector
    selector.tick = True

class Selector(selectors.BaseSelector):
    def __init__(self):
        self.tick = False
        self.list = []
        self.pools = dict()

        self.loop = lib.uv_default_loop()
        self.timer = ffi.new("uv_timer_t *")
        lib.uv_timer_init(self.loop, self.timer)
        signal.signal(signal.SIGINT, lambda sig,frame: self.sigint())
        # super().__init__(self)

    def sigint(self):
        self.interrupted = True
        pass
    def register(self, fileobj, events, data=None):
        fd = -1
        if isinstance(fileobj, int):
            fd = fileobj
        else:
            fd = fileobj.fileno()

        pass
    def unregister(self, fileobj):
        fd = -1
        if isinstance(fileobj, int):
            fd = fileobj
        else:
            fd = fileobj.fileno()
        
        try:
            pool = self.pools[fd]
            lib.uv_poll_stop(pool)
            del self.pools[fd]
        except:
            pass
        None
    def modify(self, fileobj, events, data=None):
        # fd = -1
        # if isinstance(fileobj, int):
        #     fd = fileobj
        # else:
        #     fd = fileobj.fileno()
        
        # try:
        #     del self.pools[fd]
        # except:
        #     pass
        None
    def select(timeout=None):
        self.interrupted = False

        if timeout != None:
            lib.uv_timer_stop(self.timer)
            lib.uv_timer_start(self.timer, selector_timer_handler, ffi.cast("uint64_t", int(timeout)), ffi.cast("uint64_t", 0))

        while True:
            if timeout != None and timeout <= 0:
               lib.uv_run(self.loop, lib.UV_RUN_NOWAIT)
               break
            keep_going = int(lib.uv_run(self.loop, lib.UV_RUN_ONCE))
            if not keep_going:
                break
            
            if self.interrupted:
                raise KeyboardInterrupt
            
            if self.tick:
                self.tick = False
                break
            if len(self.list):
                break
        

        return slice(self.list, 0 , len(self.list))
    def get_key(self, fileobj):
        fd = -1
        if isinstance(fileobj, int):
            fd = fileobj
        else:
            fd = fileobj.fileno()
        
        try:
            pool = self.pools[fd]
            return fd
        except:
            return None

    def get_map(self):
        None
    def close(self):
        None
    def tick(self):
        self.tick = True
    # def call_soon(self, *args, **kwargs):
    #     self.tick()
    #     return super().call_soon(*args, **kwargs)
    # def call_at(self, *args, **kwargs):
    #     self.tick()
    #     return super().call_at(*args, **kwargs)
selector = Selector()
# loop = asyncio.SelectorEventLoop(selector)
# asyncio.set_event_loop(loop)

print(selector.loop, selector.timer)