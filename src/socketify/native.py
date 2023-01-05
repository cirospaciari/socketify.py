import cffi
import platform
import os

ffi = cffi.FFI()
ffi.cdef(
    """

struct us_socket_context_options_t {
    const char *key_file_name;
    const char *cert_file_name;
    const char *passphrase;
    const char *dh_params_file_name;
    const char *ca_file_name;
    const char *ssl_ciphers;
    int ssl_prefer_low_memory_usage;
};


struct us_socket_context_t {
    struct us_loop_t *loop;
    unsigned short timestamp;
    struct us_socket_t *head;
    struct us_socket_t *iterator;
    struct us_socket_context_t *prev, *next;
    struct us_socket_t *(*on_open)(struct us_socket_t *, int is_client, char *ip, int ip_length);
    struct us_socket_t *(*on_data)(struct us_socket_t *, char *data, int length);
    struct us_socket_t *(*on_writable)(struct us_socket_t *);
    struct us_socket_t *(*on_close)(struct us_socket_t *, int code, void *reason);
    struct us_socket_t *(*on_socket_timeout)(struct us_socket_t *);
    struct us_socket_t *(*on_end)(struct us_socket_t *);
    struct us_socket_t *(*on_connect_error)(struct us_socket_t *, int code);
    int (*is_low_prio)(struct us_socket_t *);
};

struct us_poll_t {
    struct {
        signed int fd : 28;
        unsigned int poll_type : 4;
    } state;
};


struct us_socket_t {
    struct us_poll_t p;
    struct us_socket_context_t *context;
    struct us_socket_t *prev, *next;
    unsigned short timeout : 14;
    unsigned short low_prio_state : 2;
};

struct us_listen_socket_t {
    struct us_socket_t s;
    unsigned int socket_ext_size;
};
void us_listen_socket_close(int ssl, struct us_listen_socket_t *ls);
int us_socket_local_port(int ssl, struct us_listen_socket_t *ls);
struct us_loop_t *uws_get_loop();
struct us_loop_t *uws_get_loop_with_native(void* existing_native_loop);
typedef enum
{
    _COMPRESSOR_MASK = 0x00FF,
    _DECOMPRESSOR_MASK = 0x0F00,
    DISABLED = 0,
    SHARED_COMPRESSOR = 1,
    SHARED_DECOMPRESSOR = 1 << 8,
    DEDICATED_DECOMPRESSOR_32KB = 15 << 8,
    DEDICATED_DECOMPRESSOR_16KB = 14 << 8,
    DEDICATED_DECOMPRESSOR_8KB = 13 << 8,
    DEDICATED_DECOMPRESSOR_4KB = 12 << 8,
    DEDICATED_DECOMPRESSOR_2KB = 11 << 8,
    DEDICATED_DECOMPRESSOR_1KB = 10 << 8,
    DEDICATED_DECOMPRESSOR_512B = 9 << 8,
    DEDICATED_DECOMPRESSOR = 15 << 8,
    DEDICATED_COMPRESSOR_3KB = 9 << 4 | 1,
    DEDICATED_COMPRESSOR_4KB = 9 << 4 | 2,
    DEDICATED_COMPRESSOR_8KB = 10 << 4 | 3,
    DEDICATED_COMPRESSOR_16KB = 11 << 4 | 4,
    DEDICATED_COMPRESSOR_32KB = 12 << 4 | 5,
    DEDICATED_COMPRESSOR_64KB = 13 << 4 | 6,
    DEDICATED_COMPRESSOR_128KB = 14 << 4 | 7,
    DEDICATED_COMPRESSOR_256KB = 15 << 4 | 8,
    DEDICATED_COMPRESSOR = 15 << 4 | 8
} uws_compress_options_t;

typedef enum
{
    CONTINUATION = 0,
    TEXT = 1,
    BINARY = 2,
    CLOSE = 8,
    PING = 9,
    PONG = 10
} uws_opcode_t;

typedef enum
{
    BACKPRESSURE,
    SUCCESS,
    DROPPED
} uws_sendstatus_t;

typedef struct
{
    int port;
    const char *host;
    int options;
} uws_app_listen_config_t;

struct uws_app_s;
struct uws_req_s;
struct uws_res_s;
struct uws_websocket_s;
struct uws_header_iterator_s;
typedef struct uws_app_s uws_app_t;
typedef struct uws_req_s uws_req_t;
typedef struct uws_res_s uws_res_t;
typedef struct uws_socket_context_s uws_socket_context_t;
typedef struct uws_websocket_s uws_websocket_t;

typedef void (*uws_websocket_handler)(uws_websocket_t *ws, void* user_data);
typedef void (*uws_websocket_message_handler)(uws_websocket_t *ws, const char *message, size_t length, uws_opcode_t opcode, void* user_data);
typedef void (*uws_websocket_ping_pong_handler)(uws_websocket_t *ws, const char *message, size_t length, void* user_data);
typedef void (*uws_websocket_close_handler)(uws_websocket_t *ws, int code, const char *message, size_t length, void* user_data);
typedef void (*uws_websocket_upgrade_handler)(uws_res_t *response, uws_req_t *request, uws_socket_context_t *context, void* user_data);
typedef void (*uws_websocket_subscription_handler)(uws_websocket_t *ws, const char *topic_name, size_t topic_name_length, int new_number_of_subscriber, int old_number_of_subscriber, void* user_data);

typedef struct
{
    uws_compress_options_t compression;
    unsigned int maxPayloadLength;
    unsigned short idleTimeout;
    unsigned int maxBackpressure;
    bool closeOnBackpressureLimit;
    bool resetIdleTimeoutOnSend;
    bool sendPingsAutomatically;
    unsigned short maxLifetime;
    uws_websocket_upgrade_handler upgrade;
    uws_websocket_handler open;
    uws_websocket_message_handler message;
    uws_websocket_handler drain;
    uws_websocket_ping_pong_handler ping;
    uws_websocket_ping_pong_handler pong;
    uws_websocket_close_handler close;
    uws_websocket_subscription_handler subscription;
} uws_socket_behavior_t;

typedef struct {
    bool ok;
    bool has_responded;
} uws_try_end_result_t;

typedef void (*uws_listen_handler)(struct us_listen_socket_t *listen_socket, uws_app_listen_config_t config, void *user_data);
typedef void (*uws_listen_domain_handler)(struct us_listen_socket_t *listen_socket, const char* domain, size_t domain_length, int options, void *user_data);
typedef void (*uws_method_handler)(uws_res_t *response, uws_req_t *request, void *user_data);
typedef void (*uws_filter_handler)(uws_res_t *response, int, void *user_data);
typedef void (*uws_missing_server_handler)(const char *hostname, size_t hostname_length, void *user_data);
typedef void (*uws_get_headers_server_handler)(const char *header_name, size_t header_name_size, const char *header_value, size_t header_value_size, void *user_data);


uws_app_t *uws_create_app(int ssl, struct us_socket_context_options_t options);
void uws_app_destroy(int ssl, uws_app_t *app);
void uws_app_get(int ssl, uws_app_t *app, const char *pattern, uws_method_handler handler, void *user_data);
void uws_app_post(int ssl, uws_app_t *app, const char *pattern, uws_method_handler handler, void *user_data);
void uws_app_options(int ssl, uws_app_t *app, const char *pattern, uws_method_handler handler, void *user_data);
void uws_app_delete(int ssl, uws_app_t *app, const char *pattern, uws_method_handler handler, void *user_data);
void uws_app_patch(int ssl, uws_app_t *app, const char *pattern, uws_method_handler handler, void *user_data);
void uws_app_put(int ssl, uws_app_t *app, const char *pattern, uws_method_handler handler, void *user_data);
void uws_app_head(int ssl, uws_app_t *app, const char *pattern, uws_method_handler handler, void *user_data);
void uws_app_connect(int ssl, uws_app_t *app, const char *pattern, uws_method_handler handler, void *user_data);
void uws_app_trace(int ssl, uws_app_t *app, const char *pattern, uws_method_handler handler, void *user_data);
void uws_app_any(int ssl, uws_app_t *app, const char *pattern, uws_method_handler handler, void *user_data);

void uws_app_run(int ssl, uws_app_t *);

void uws_app_listen(int ssl, uws_app_t *app, int port, uws_listen_handler handler, void *user_data);
void uws_app_listen_with_config(int ssl, uws_app_t *app, uws_app_listen_config_t config, uws_listen_handler handler, void *user_data);
void uws_app_listen_domain(int ssl, uws_app_t *app, const char *domain, size_t domain_length, uws_listen_domain_handler handler, void *user_data);
void uws_app_listen_domain_with_options(int ssl, uws_app_t *app, const char *domain,size_t domain_length, int options, uws_listen_domain_handler handler, void *user_data);
bool uws_constructor_failed(int ssl, uws_app_t *app);
unsigned int uws_num_subscribers(int ssl, uws_app_t *app, const char *topic, size_t topic_length);
bool uws_publish(int ssl, uws_app_t *app, const char *topic, size_t topic_length, const char *message, size_t message_length, uws_opcode_t opcode, bool compress);
void *uws_get_native_handle(int ssl, uws_app_t *app);
void uws_remove_server_name(int ssl, uws_app_t *app, const char *hostname_pattern, size_t hostname_pattern_length);
void uws_add_server_name(int ssl, uws_app_t *app, const char *hostname_pattern, size_t hostname_pattern_length);
void uws_add_server_name_with_options(int ssl, uws_app_t *app, const char *hostname_pattern, size_t hostname_pattern_length, struct us_socket_context_options_t options);
void uws_missing_server_name(int ssl, uws_app_t *app, uws_missing_server_handler handler, void *user_data);
void uws_filter(int ssl, uws_app_t *app, uws_filter_handler handler, void *user_data);


void uws_res_end(int ssl, uws_res_t *res, const char *data, size_t length, bool close_connection);
void uws_res_pause(int ssl, uws_res_t *res);
void uws_res_resume(int ssl, uws_res_t *res);
void uws_res_write_continue(int ssl, uws_res_t *res);
void uws_res_write_status(int ssl, uws_res_t *res, const char *status, size_t length);
void uws_res_write_header(int ssl, uws_res_t *res, const char *key, size_t key_length, const char *value, size_t value_length);
void uws_res_override_write_offset(int ssl, uws_res_t *res, uintmax_t offset);

void uws_res_write_header_int(int ssl, uws_res_t *res, const char *key, size_t key_length, uint64_t value);
void uws_res_end_without_body(int ssl, uws_res_t *res, bool close_connection);
bool uws_res_write(int ssl, uws_res_t *res, const char *data, size_t length);
uintmax_t uws_res_get_write_offset(int ssl, uws_res_t *res);
void *uws_res_get_native_handle(int ssl, uws_res_t *res);
bool uws_res_has_responded(int ssl, uws_res_t *res);
void uws_res_on_writable(int ssl, uws_res_t *res, bool (*handler)(uws_res_t *res, uintmax_t, void *opcional_data), void *user_data);
void uws_res_on_aborted(int ssl, uws_res_t *res, void (*handler)(uws_res_t *res, void *opcional_data), void *opcional_data);
void uws_res_on_data(int ssl, uws_res_t *res, void (*handler)(uws_res_t *res, const char *chunk, size_t chunk_length, bool is_end, void *opcional_data), void *opcional_data);
void uws_res_upgrade(int ssl, uws_res_t *res, void *data, const char *sec_web_socket_key, size_t sec_web_socket_key_length, const char *sec_web_socket_protocol, size_t sec_web_socket_protocol_length, const char *sec_web_socket_extensions, size_t sec_web_socket_extensions_length, uws_socket_context_t *ws);
uws_try_end_result_t uws_res_try_end(int ssl, uws_res_t *res, const char *data, size_t length, uintmax_t total_size, bool close_connection);
void uws_res_cork(int ssl, uws_res_t *res,void(*callback)(uws_res_t *res, void* user_data) ,void* user_data);
size_t uws_res_get_remote_address(int ssl, uws_res_t *res, const char **dest);
size_t uws_res_get_remote_address_as_text(int ssl, uws_res_t *res, const char **dest);
size_t uws_res_get_proxied_remote_address(int ssl, uws_res_t *res, const char **dest);
size_t uws_res_get_proxied_remote_address_as_text(int ssl, uws_res_t *res, const char **dest);

bool uws_req_is_ancient(uws_req_t *res);
bool uws_req_get_yield(uws_req_t *res);
void uws_req_set_field(uws_req_t *res, bool yield);
size_t uws_req_get_url(uws_req_t *res, const char **dest);
size_t uws_req_get_method(uws_req_t *res, const char **dest);
size_t uws_req_get_case_sensitive_method(uws_req_t *res, const char **dest);

size_t uws_req_get_header(uws_req_t *res, const char *lower_case_header, size_t lower_case_header_length, const char **dest);
size_t uws_req_get_query(uws_req_t *res, const char *key, size_t key_length, const char **dest);
size_t uws_req_get_parameter(uws_req_t *res, unsigned short index, const char **dest);
size_t uws_req_get_full_url(uws_req_t *res, const char **dest);
void uws_req_for_each_header(uws_req_t *res, uws_get_headers_server_handler handler, void *user_data);

void uws_ws(int ssl, uws_app_t *app, const char *pattern, uws_socket_behavior_t behavior, void* user_data);
void *uws_ws_get_user_data(int ssl, uws_websocket_t *ws);
void uws_ws_close(int ssl, uws_websocket_t *ws);
uws_sendstatus_t uws_ws_send(int ssl, uws_websocket_t *ws, const char *message, size_t length, uws_opcode_t opcode);
uws_sendstatus_t uws_ws_send_with_options(int ssl, uws_websocket_t *ws, const char *message, size_t length, uws_opcode_t opcode, bool compress, bool fin);
uws_sendstatus_t uws_ws_send_fragment(int ssl, uws_websocket_t *ws, const char *message, size_t length, bool compress);
uws_sendstatus_t uws_ws_send_first_fragment(int ssl, uws_websocket_t *ws, const char *message, size_t length, bool compress);
uws_sendstatus_t uws_ws_send_first_fragment_with_opcode(int ssl, uws_websocket_t *ws, const char *message, size_t length, uws_opcode_t opcode, bool compress);
uws_sendstatus_t uws_ws_send_last_fragment(int ssl, uws_websocket_t *ws, const char *message, size_t length, bool compress);
void uws_ws_end(int ssl, uws_websocket_t *ws, int code, const char *message, size_t length);
void uws_ws_cork(int ssl, uws_websocket_t *ws, void (*handler)(void *user_data), void *user_data);

bool uws_ws_subscribe(int ssl, uws_websocket_t *ws, const char *topic, size_t length);
bool uws_ws_unsubscribe(int ssl, uws_websocket_t *ws, const char *topic, size_t length);
bool uws_ws_is_subscribed(int ssl, uws_websocket_t *ws, const char *topic, size_t length);
void uws_ws_iterate_topics(int ssl, uws_websocket_t *ws, void (*callback)(const char *topic, size_t length, void *user_data), void *user_data);
bool uws_ws_publish(int ssl, uws_websocket_t *ws, const char *topic, size_t topic_length, const char *message, size_t message_length);
bool uws_ws_publish_with_options(int ssl, uws_websocket_t *ws, const char *topic, size_t topic_length, const char *message, size_t message_length, uws_opcode_t opcode, bool compress);
int uws_ws_get_buffered_amount(int ssl, uws_websocket_t *ws);
size_t uws_ws_get_remote_address(int ssl, uws_websocket_t *ws, const char **dest);
size_t uws_ws_get_remote_address_as_text(int ssl, uws_websocket_t *ws, const char **dest);



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

typedef struct {

  const char* name;
  const char* value;
  
  size_t name_size;
  size_t value_size;
  
  void* next;
} socketify_header;


typedef struct {

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

typedef struct {

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

typedef void (*socketify_asgi_method_handler)(int ssl, uws_res_t *response, socketify_asgi_data request, void *user_data, bool* aborted);
typedef struct {
  int ssl;
  uws_app_t* app;
  socketify_asgi_method_handler handler;
  void * user_data;
} socksocketify_asgi_app_info;
typedef void (*socketify_asgi_ws_method_handler)(int ssl, uws_res_t *response, socketify_asgi_ws_data request, uws_socket_context_t* socket, void *user_data, bool* aborted);
typedef struct {
  int ssl;
  uws_app_t* app;
  socketify_asgi_ws_method_handler handler;
  uws_socket_behavior_t behavior;
  void * user_data;
} socksocketify_asgi_ws_app_info;

socketify_asgi_data socketify_asgi_request(int ssl, uws_req_t *req, uws_res_t *res);
void socketify_destroy_headers(socketify_header* headers);
bool socketify_res_write_int_status_with_headers(int ssl, uws_res_t* res, int code, socketify_header* headers);
void socketify_res_write_headers(int ssl, uws_res_t* res, socketify_header* headers);
socketify_asgi_ws_data socketify_asgi_ws_request(int ssl, uws_req_t *req, uws_res_t *res);
bool socketify_res_write_int_status(int ssl, uws_res_t* res, int code);
socksocketify_asgi_app_info* socketify_add_asgi_http_handler(int ssl, uws_app_t* app, socketify_asgi_method_handler handler, void* user_data);
void socketify_destroy_asgi_app_info(socksocketify_asgi_app_info* app);
socksocketify_asgi_ws_app_info* socketify_add_asgi_ws_handler(int ssl, uws_app_t* app, uws_socket_behavior_t behavior, socketify_asgi_ws_method_handler handler, void* user_data);
void socketify_destroy_asgi_ws_app_info(socksocketify_asgi_ws_app_info* app);

void socketify_res_cork_write(int ssl, uws_res_t *response, const char* data, size_t length);
void socketify_res_cork_end(int ssl, uws_res_t *response, const char* data, size_t length, bool close_connection);
void socketify_ws_cork_send(int ssl, uws_websocket_t *ws, const char* data, size_t length, uws_opcode_t opcode);


void socketify_ws_cork_send_with_options(int ssl, uws_websocket_t *ws, const char* data, size_t length, uws_opcode_t opcode, bool compress, bool close_connection);
"""
)

library_extension = "dll" if platform.system().lower() == "windows" else "so"
library_path = os.path.join(
    os.path.dirname(__file__),
    "libsocketify_%s_%s.%s"
    % (
        platform.system().lower(),
        "arm64" if "arm" in platform.processor().lower() else "amd64",
        library_extension,
    ),
)


lib = ffi.dlopen(library_path)


