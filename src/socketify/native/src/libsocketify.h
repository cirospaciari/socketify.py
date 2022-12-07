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


DLL_EXPORT typedef struct {

  const char* name;
  const char* value;
  
  size_t name_size;
  size_t value_size;
  
  void* next;
} socketify_header;


DLL_EXPORT typedef struct {

  const char* full_url;
  const char* url;
  const char* query_string;
  const char* method;
  const char* remote_address;

  size_t full_url_size;
  size_t url_size;
  size_t query_string_size;
  size_t method_size;
  size_t remote_address_size;

  socketify_header* header_list;

  bool has_content;
} socketify_asgi_data;

DLL_EXPORT typedef struct {

  const char* full_url;
  const char* url;
  const char* query_string;
  const char* method;
  const char* remote_address;

  size_t full_url_size;
  size_t url_size;
  size_t query_string_size;
  size_t method_size;
  size_t remote_address_size;

  const char* protocol;
  const char* key;
  const char* extensions;
  size_t protocol_size;
  size_t key_size;
  size_t extensions_size;

  socketify_header* header_list;
} socketify_asgi_ws_data;

DLL_EXPORT typedef void (*socketify_asgi_method_handler)(int ssl, uws_res_t *response, socketify_asgi_data request, void *user_data, bool* aborted);
DLL_EXPORT typedef void (*socketify_asgi_ws_method_handler)(int ssl, uws_res_t *response, socketify_asgi_ws_data request, uws_socket_context_t* socket, void *user_data, bool* aborted);
DLL_EXPORT typedef struct {
  int ssl;
  uws_app_t* app;
  socketify_asgi_method_handler handler;
  void * user_data;
} socksocketify_asgi_app_info;

DLL_EXPORT typedef struct {
  int ssl;
  uws_app_t* app;
  socketify_asgi_ws_method_handler handler;
  uws_socket_behavior_t behavior;
  void * user_data;
} socksocketify_asgi_ws_app_info;


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

DLL_EXPORT socketify_asgi_data socketify_asgi_request(int ssl, uws_req_t *req, uws_res_t *res);
DLL_EXPORT void socketify_destroy_headers(socketify_header* headers);
DLL_EXPORT bool socketify_res_write_int_status_with_headers(int ssl, uws_res_t* res, int code, socketify_header* headers);
DLL_EXPORT void socketify_res_write_headers(int ssl, uws_res_t* res, socketify_header* headers);
DLL_EXPORT bool socketify_res_write_int_status(int ssl, uws_res_t* res, int code);
DLL_EXPORT socketify_asgi_ws_data socketify_asgi_ws_request(int ssl, uws_req_t *req, uws_res_t *res);

DLL_EXPORT socksocketify_asgi_app_info* socketify_add_asgi_http_handler(int ssl, uws_app_t* app, socketify_asgi_method_handler handler, void* user_data);
DLL_EXPORT void socketify_destroy_asgi_app_info(socksocketify_asgi_app_info* app);

DLL_EXPORT void socketify_res_cork_write(int ssl, uws_res_t *response, const char* data, size_t length);
DLL_EXPORT void socketify_res_cork_end(int ssl, uws_res_t *response, const char* data, size_t length, bool close_connection);

DLL_EXPORT socksocketify_asgi_ws_app_info* socketify_add_asgi_ws_handler(int ssl, uws_app_t* app, uws_socket_behavior_t behavior, socketify_asgi_ws_method_handler handler, void* user_data);
DLL_EXPORT void socketify_destroy_asgi_ws_app_info(socksocketify_asgi_ws_app_info* app);
DLL_EXPORT void socketify_ws_cork_send(int ssl, uws_websocket_t *ws, const char* data, size_t length, uws_opcode_t opcode);
DLL_EXPORT void socketify_ws_cork_send_with_options(int ssl, uws_websocket_t *ws, const char* data, size_t length, uws_opcode_t opcode, bool compress, bool fin);
#endif
#ifdef __cplusplus
}
#endif