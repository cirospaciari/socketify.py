#ifndef SOCKETIFY_CAPI_HEADER
#define SOCKETIFY_CAPI_HEADER
#include "uv.h"
#include <stdbool.h>


typedef void (*socketify_prepare_handler)(void* user_data);
typedef void (*socketify_timer_handler)(void* user_data);

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
void socketify_timer_set_repeat(socketify_timer* timer, uint64_t repeat);

#endif