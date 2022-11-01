
import cffi
import os

ffi = cffi.FFI()
ffi.cdef("""


typedef void (*socketify_prepare_handler)(void* user_data);
typedef void (*socketify_timer_handler)(void* user_data);
typedef void (*socketify_async_handler)(void* user_data);

typedef enum {
  SOCKETIFY_RUN_DEFAULT = 0,
  SOCKETIFY_RUN_ONCE,
  SOCKETIFY_RUN_NOWAIT
} socketify_run_mode;

typedef struct {
    void* uv_prepare_ptr;
    socketify_prepare_handler on_prepare_handler;
    void* on_prepare_data;
    void* uv_loop;
} socketify_loop;

typedef struct{
    void* uv_timer_ptr;
    socketify_timer_handler handler;
    void* user_data;
} socketify_timer;

typedef struct{
    void* uv_async_ptr;
    socketify_async_handler handler;
    void* user_data;
} socketify_async;

socketify_loop * socketify_create_loop();
bool socketify_constructor_failed(socketify_loop* loop);
bool socketify_on_prepare(socketify_loop* loop, socketify_prepare_handler handler, void* user_data);
bool socketify_prepare_unbind(socketify_loop* loop);
void socketify_destroy_loop(socketify_loop* loop);
void* socketify_get_native_loop(socketify_loop* loop);

int socketify_loop_run(socketify_loop* loop, socketify_run_mode mode);
void socketify_loop_stop(socketify_loop* loop);

socketify_timer* socketify_create_timer(socketify_loop* loop, uint64_t timeout, uint64_t repeat, socketify_timer_handler handler, void* user_data);
void socketify_timer_destroy(socketify_timer* timer);
bool socketify_async_call(socketify_loop* loop, socketify_async_handler handler, void* user_data);
void socketify_timer_set_repeat(socketify_timer* timer, uint64_t repeat);


socketify_timer* socketify_create_check(socketify_loop* loop, socketify_timer_handler handler, void* user_data);
void socketify_check_destroy(socketify_timer* timer);
""")
library_path = os.path.join(os.path.dirname(__file__), "libsocketify.so")

lib = ffi.dlopen(library_path)

@ffi.callback("void(void *)")
def socketify_generic_handler(data):
    if not data == ffi.NULL:
        (handler, user_data) = ffi.from_handle(data)
        handler(user_data)
        

class UVCheck:
    def __init__(self, loop, handler, user_data):
        self._handler_data = ffi.new_handle((handler, user_data))
        self._ptr = lib.socketify_create_check(loop, socketify_generic_handler, self._handler_data)
    def stop(self):
        lib.socketify_check_destroy(self._ptr)
        self._handler_data = None
        self._ptr = ffi.NULL

    def __del__(self):
        if self._ptr != ffi.NULL:
            lib.socketify_check_destroy(self._ptr)
            self._handler_data = None

class UVTimer:
    def __init__(self, loop, timeout, repeat, handler, user_data):
        self._handler_data = ffi.new_handle((handler, user_data))
        self._ptr = lib.socketify_create_timer(loop, ffi.cast("uint64_t", timeout), ffi.cast("uint64_t", repeat), socketify_generic_handler, self._handler_data)
    def stop(self):
        lib.socketify_timer_destroy(self._ptr)
        self._handler_data = None
        self._ptr = ffi.NULL

    def set_repeat(self, repeat):
        lib.socketify_timer_set_repeat(self._ptr, ffi.cast("uint64_t", repeat))
        
    def __del__(self):
        if self._ptr != ffi.NULL:
            lib.socketify_timer_destroy(self._ptr)
            self._handler_data = None


class UVLoop:
    def __init__(self, exception_handler=None):
        self._loop = lib.socketify_create_loop()
        if bool(lib.socketify_constructor_failed(self._loop)):
            raise RuntimeError("Failed to create socketify uv loop")

    def on_prepare(self, handler, user_data):
        self._handler_data = ffi.new_handle((handler, user_data))
        lib.socketify_on_prepare(self._loop, socketify_generic_handler, self._handler_data)

    def create_timer(self, timeout, repeat, handler, user_data):
        return UVTimer(self._loop, timeout, repeat, handler, user_data)

    def create_check(self, handler, user_data):
        return UVCheck(self._loop, handler, user_data)
        
    def prepare_unbind(self):
        lib.socketify_prepare_unbind(self._loop)

    def get_native_loop(self):
        return lib.socketify_get_native_loop(self._loop)

    def __del__(self):
        lib.socketify_destroy_loop(self._loop)
        self._handler_data = None
  
    def run(self):
        return lib.socketify_loop_run(self._loop, lib.SOCKETIFY_RUN_DEFAULT)

    def run_once(self):
        return lib.socketify_loop_run(self._loop, lib.SOCKETIFY_RUN_ONCE)

    def stop(self):
        lib.socketify_loop_stop(self._loop)