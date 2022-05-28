
import cffi
import os
# from ctypes.util import find_library
# print("libuv1: %s" % find_library('uv'))

ffi = cffi.FFI()
ffi.cdef("""


typedef struct uv_handle_t uv_handle_t;
typedef struct uv_timer_s uv_timer_t;
typedef void(*uv_timer_cb)(uv_timer_t* handle);

struct uv_timer_s {
  uv_handle_t* next_closing;                                                  \
  unsigned int flags;     
  uv_timer_cb timer_cb;                                                       \
  void* heap_node[3];                                                         \
  uint64_t timeout;                                                           \
  uint64_t repeat;                                                            \
  uint64_t start_id;
};
typedef struct uv_poll_t uv_poll_t;


typedef struct uv_loop_t uv_loop_t;

typedef struct uv_os_sock_t uv_os_sock_t;
typedef struct uv_poll_cb uv_poll_cb;

typedef void (*uv_close_cb)(uv_handle_t* handle);

typedef enum {
  UV_RUN_DEFAULT = 0,
  UV_RUN_ONCE,
  UV_RUN_NOWAIT
} uv_run_mode;

int uv_run(uv_loop_t*, uv_run_mode mode);
void uv_stop(uv_loop_t*);
int uv_poll_init(uv_loop_t* loop, uv_poll_t* handle, int fd);
int uv_poll_init_socket(uv_loop_t* loop, uv_poll_t* handle, uv_os_sock_t socket);
int uv_poll_start(uv_poll_t* handle, int events, uv_poll_cb cb);
int uv_poll_stop(uv_poll_t* handle);
void uv_close(uv_handle_t* handle, uv_close_cb close_cb);
uv_loop_t* uv_handle_get_loop(const uv_handle_t* handle);
int uv_timer_init(uv_loop_t*, uv_timer_t* handle);
int uv_timer_start(uv_timer_t* handle,
                             uv_timer_cb cb,
                             uint64_t timeout,
                             uint64_t repeat);
int uv_timer_stop(uv_timer_t* handle);
uv_loop_t* uv_default_loop(void);
""")

lib = ffi.dlopen("uv")
