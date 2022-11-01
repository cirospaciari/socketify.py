#include "uv.h"
#include "libsocketify.h"
#include <stdlib.h>
#include <stdio.h>
#include "libuwebsockets.h"
#include "libuwebsockets.cpp" //include symbols

extern "C"
{
void socketify_generic_prepare_callback(uv_prepare_t *prepare){
    socketify_loop* loop = (socketify_loop*)uv_handle_get_data((uv_handle_t*)prepare);
    loop->on_prepare_handler(loop->on_prepare_data);
}

void socketify_generic_timer_callback(uv_timer_t *timer){
    socketify_timer* loop_data = (socketify_timer*)uv_handle_get_data((uv_handle_t*)timer);
    loop_data->handler(loop_data->user_data);
}

void socketify_generic_check_callback(uv_check_t *timer){
    socketify_timer* loop_data = (socketify_timer*)uv_handle_get_data((uv_handle_t*)timer);
    loop_data->handler(loop_data->user_data);
}


void* socketify_get_native_loop(socketify_loop* loop){
    return loop->uv_loop;
}

socketify_loop * socketify_create_loop(){
    socketify_loop* loop = (socketify_loop*)malloc(sizeof(uv_prepare_t));
    loop->uv_loop = NULL;
    loop->on_prepare_handler = NULL;
    loop->uv_prepare_ptr = NULL;

    uv_loop_t* uv_loop = (uv_loop_t*)malloc(sizeof(uv_loop_t));
    if(uv_loop_init(uv_loop)){
        free(uv_loop);
        return loop;
    }
    loop->uv_loop = uv_loop;
    return loop;
}

bool socketify_constructor_failed(socketify_loop* loop){
    return loop->uv_loop == NULL;
}

bool socketify_on_prepare(socketify_loop* loop, socketify_prepare_handler handler, void* user_data){
    if (loop->uv_prepare_ptr != NULL) return false;
    if(handler == NULL) return false;
    uv_prepare_t* prepare = (uv_prepare_t*)malloc(sizeof(uv_prepare_t));
    if(uv_prepare_init((uv_loop_t*)loop->uv_loop, prepare)){
        free(prepare);
        return false;
    }
    
    loop->on_prepare_handler = handler;
    loop->on_prepare_data = user_data;
    loop->uv_prepare_ptr = prepare;
    uv_handle_set_data((uv_handle_t*)prepare, loop);
    uv_prepare_start(prepare, socketify_generic_prepare_callback);

    return true;
    // uv_unref((uv_handle_t *) loop->uv_pre);
    // loop->uv_pre->data = loop;
}

bool socketify_prepare_unbind(socketify_loop* loop){
    if(loop->uv_prepare_ptr == NULL) return false;
    uv_prepare_stop((uv_prepare_t *)loop->uv_prepare_ptr);

    free(loop->uv_prepare_ptr);
    loop->uv_prepare_ptr = NULL;
    return true;
}

int socketify_loop_run(socketify_loop* loop, socketify_run_mode mode){
    return uv_run((uv_loop_t*)loop->uv_loop, (uv_run_mode)mode);
}

void socketify_loop_stop(socketify_loop* loop){
     if(uv_loop_alive((uv_loop_t*)loop->uv_loop)){
        uv_stop((uv_loop_t*)loop->uv_loop);
    }
}

void socketify_destroy_loop(socketify_loop* loop){
    socketify_loop_stop(loop);

    uv_loop_close((uv_loop_t*)loop->uv_loop);
    free(loop->uv_loop);
    if(loop->uv_prepare_ptr){
        free(loop->uv_prepare_ptr);
    }
    free(loop);
}

socketify_timer* socketify_create_timer(socketify_loop* loop, uint64_t timeout, uint64_t repeat, socketify_timer_handler handler, void* user_data){
       
    uv_timer_t* uv_timer = (uv_timer_t* ) malloc(sizeof(uv_timer_t));
    
    if(uv_timer_init((uv_loop_t*)loop->uv_loop, uv_timer)){
         free(uv_timer);
         return NULL;
    }

    socketify_timer* timer = (socketify_timer*)malloc(sizeof(socketify_timer));
    timer->uv_timer_ptr = uv_timer;
    timer->user_data = user_data;
    timer->handler = handler;

    uv_handle_set_data((uv_handle_t*)uv_timer, timer);
    uv_timer_start(uv_timer, socketify_generic_timer_callback, timeout, repeat); 

    return timer;
}

void socketify_timer_set_repeat(socketify_timer* timer, uint64_t repeat){
    uv_timer_set_repeat((uv_timer_t *) timer->uv_timer_ptr, repeat);
}


//stops and destroy timer info
void socketify_timer_destroy(socketify_timer* timer){
    uv_timer_stop((uv_timer_t *)timer->uv_timer_ptr);
    free(timer->uv_timer_ptr);
    free(timer);
}



socketify_timer* socketify_create_check(socketify_loop* loop, socketify_timer_handler handler, void* user_data){
       
    uv_check_t* uv_timer = (uv_check_t*)malloc(sizeof(uv_check_t));
    if(uv_check_init((uv_loop_t*)loop->uv_loop, uv_timer)){
         free(uv_timer);
         return NULL;
    }

    socketify_timer* timer = (socketify_timer*)malloc(sizeof(socketify_timer));
    timer->uv_timer_ptr = uv_timer;
    timer->user_data = user_data;
    timer->handler = handler;

    uv_handle_set_data((uv_handle_t*)uv_timer, timer);
    uv_check_start(uv_timer, socketify_generic_check_callback); 

    return timer;
}

//stops and destroy timer info
void socketify_check_destroy(socketify_timer* timer){
    uv_check_stop((uv_check_t *)timer->uv_timer_ptr);
    free(timer->uv_timer_ptr);
    free(timer);
}
}