#ifndef SOCKETIFY_CAPI_HEADER
#define SOCKETIFY_CAPI_HEADER
#include "uv.h"
#include <stdbool.h>
#include "libuwebsockets.h"

#ifdef __cplusplus
extern "C"
{
#endif
DLL_EXPORT typedef void (*socketify_prepare_handler)(void* user_data);
DLL_EXPORT typedef void (*socketify_timer_handler)(void* user_data);

DLL_EXPORT typedef enum {
  SOCKETIFY_RUN_DEFAULT = 0,
  SOCKETIFY_RUN_ONCE,
  SOCKETIFY_RUN_NOWAIT
} socketify_run_mode;

DLL_EXPORT typedef struct {
    void* uv_prepare_ptr;
    socketify_prepare_handler on_prepare_handler;
    void* on_prepare_data;
    void* uv_loop;
} socketify_loop;

DLL_EXPORT typedef struct{
    void* uv_timer_ptr;
    socketify_timer_handler handler;
    void* user_data;
} socketify_timer;



DLL_EXPORT socketify_loop * socketify_create_loop();
DLL_EXPORT bool socketify_constructor_failed(socketify_loop* loop);
DLL_EXPORT bool socketify_on_prepare(socketify_loop* loop, socketify_prepare_handler handler, void* user_data);
DLL_EXPORT bool socketify_prepare_unbind(socketify_loop* loop);
DLL_EXPORT void socketify_destroy_loop(socketify_loop* loop);
DLL_EXPORT void* socketify_get_native_loop(socketify_loop* loop);

DLL_EXPORT int socketify_loop_run(socketify_loop* loop, socketify_run_mode mode);
DLL_EXPORT void socketify_loop_stop(socketify_loop* loop);

DLL_EXPORT socketify_timer* socketify_create_timer(socketify_loop* loop, uint64_t timeout, uint64_t repeat, socketify_timer_handler handler, void* user_data);
DLL_EXPORT void socketify_timer_destroy(socketify_timer* timer);
DLL_EXPORT void socketify_timer_set_repeat(socketify_timer* timer, uint64_t repeat);

DLL_EXPORT socketify_timer* socketify_create_check(socketify_loop* loop, socketify_timer_handler handler, void* user_data);
DLL_EXPORT void socketify_check_destroy(socketify_timer* timer);
#endif
#ifdef __cplusplus
}
#endif