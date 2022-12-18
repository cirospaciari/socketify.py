from .native import ffi, lib


@ffi.callback("void(void *)")
def socketify_generic_handler(data):
    if not data == ffi.NULL:
        (handler, user_data) = ffi.from_handle(data)
        handler(user_data)

class UVCheck:
    def __init__(self, loop, handler, user_data):
        self._handler_data = ffi.new_handle((handler, user_data))
        self._ptr = lib.socketify_create_check(
            loop, socketify_generic_handler, self._handler_data
        )

    def stop(self):
        lib.socketify_check_destroy(self._ptr)
        self._ptr = ffi.NULL

    def __del__(self):
        if self._ptr != ffi.NULL:
            lib.socketify_check_destroy(self._ptr)


class UVTimer:
    def __init__(self, loop, timeout, repeat, handler, user_data):
        self._handler_data = ffi.new_handle((handler, user_data))
        self._ptr = lib.socketify_create_timer(
            loop,
            ffi.cast("uint64_t", timeout),
            ffi.cast("uint64_t", repeat),
            socketify_generic_handler,
            self._handler_data,
        )

    def stop(self):
        lib.socketify_timer_destroy(self._ptr)
        self._ptr = ffi.NULL

    def set_repeat(self, repeat):
        lib.socketify_timer_set_repeat(self._ptr, ffi.cast("uint64_t", repeat))

    def __del__(self):
        if self._ptr != ffi.NULL:
            lib.socketify_timer_destroy(self._ptr)


class UVLoop:
    def __init__(self, exception_handler=None):
        self._loop = lib.socketify_create_loop()
        if bool(lib.socketify_constructor_failed(self._loop)):
            raise RuntimeError("Failed to create socketify uv loop")

    def on_prepare(self, handler, user_data):
        self._handler_data = ffi.new_handle((handler, user_data))
        lib.socketify_on_prepare(
            self._loop, socketify_generic_handler, self._handler_data
        )

    def create_timer(self, timeout, repeat, handler, user_data):
        return UVTimer(self._loop, timeout, repeat, handler, user_data)

    def create_check(self, handler, user_data):
        return UVCheck(self._loop, handler, user_data)

    def prepare_unbind(self):
        lib.socketify_prepare_unbind(self._loop)

    def get_native_loop(self):
        return lib.socketify_get_native_loop(self._loop)

    def dispose(self):
        if self._loop != ffi.NULL:
            lib.socketify_destroy_loop(self._loop)
            self._handler_data = None
            self._loop = ffi.NULL

    def __del__(self):
        if self._loop != ffi.NULL:
            lib.socketify_destroy_loop(self._loop)
            self._handler_data = None
            self._loop = ffi.NULL

    def run_nowait(self):
        if self._loop != ffi.NULL:
            return lib.socketify_loop_run(self._loop, lib.SOCKETIFY_RUN_NOWAIT)
        
    def run(self):
        if self._loop != ffi.NULL:
            return lib.socketify_loop_run(self._loop, lib.SOCKETIFY_RUN_DEFAULT)

    def run_once(self):
        if self._loop != ffi.NULL:
            return lib.socketify_loop_run(self._loop, lib.SOCKETIFY_RUN_ONCE)

    def stop(self):
        if self._loop != ffi.NULL:
            lib.socketify_loop_stop(self._loop)
