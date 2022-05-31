import cffi
import os
from .loop import Loop
from .status_codes import status_codes
import json
import inspect

ffi = cffi.FFI()
ffi.cdef("""

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
typedef void (*uws_websocket_handler)(uws_websocket_t *ws);
typedef void (*uws_websocket_message_handler)(uws_websocket_t *ws, const char *message, size_t length, uws_opcode_t opcode);
typedef void (*uws_websocket_ping_pong_handler)(uws_websocket_t *ws, const char *message, size_t length);
typedef void (*uws_websocket_close_handler)(uws_websocket_t *ws, int code, const char *message, size_t length);
typedef void (*uws_websocket_upgrade_handler)(uws_res_t *response, uws_req_t *request, uws_socket_context_t *context);

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
} uws_socket_behavior_t;


typedef void (*uws_listen_handler)(struct us_listen_socket_t *listen_socket, uws_app_listen_config_t config, void *user_data);
typedef void (*uws_method_handler)(uws_res_t *response, uws_req_t *request, void *user_data);
typedef void (*uws_filter_handler)(uws_res_t *response, int, void *user_data);
typedef void (*uws_missing_server_handler)(const char *hostname, void *user_data);
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
bool uws_constructor_failed(int ssl, uws_app_t *app);
unsigned int uws_num_subscribers(int ssl, uws_app_t *app, const char *topic);
bool uws_publish(int ssl, uws_app_t *app, const char *topic, size_t topic_length, const char *message, size_t message_length, uws_opcode_t opcode, bool compress);
void *uws_get_native_handle(int ssl, uws_app_t *app);
void uws_remove_server_name(int ssl, uws_app_t *app, const char *hostname_pattern);
void uws_add_server_name(int ssl, uws_app_t *app, const char *hostname_pattern);
void uws_add_server_name_with_options(int ssl, uws_app_t *app, const char *hostname_pattern, struct us_socket_context_options_t options);
void uws_missing_server_name(int ssl, uws_app_t *app, uws_missing_server_handler handler, void *user_data);
void uws_filter(int ssl, uws_app_t *app, uws_filter_handler handler, void *user_data);



void uws_res_end(int ssl, uws_res_t *res, const char *data, size_t length, bool close_connection);
void uws_res_pause(int ssl, uws_res_t *res);
void uws_res_resume(int ssl, uws_res_t *res);
void uws_res_write_continue(int ssl, uws_res_t *res);
void uws_res_write_status(int ssl, uws_res_t *res, const char *status, size_t length);
void uws_res_write_header(int ssl, uws_res_t *res, const char *key, size_t key_length, const char *value, size_t value_length);

void uws_res_write_header_int(int ssl, uws_res_t *res, const char *key, size_t key_length, uint64_t value);
void uws_res_end_without_body(int ssl, uws_res_t *res);
bool uws_res_write(int ssl, uws_res_t *res, const char *data, size_t length);
uintmax_t uws_res_get_write_offset(int ssl, uws_res_t *res);
bool uws_res_has_responded(int ssl, uws_res_t *res);
void uws_res_on_writable(int ssl, uws_res_t *res, bool (*handler)(uws_res_t *res, uintmax_t, void *opcional_data), void *user_data);
void uws_res_on_aborted(int ssl, uws_res_t *res, void (*handler)(uws_res_t *res, void *opcional_data), void *opcional_data);
void uws_res_on_data(int ssl, uws_res_t *res, void (*handler)(uws_res_t *res, const char *chunk, size_t chunk_length, bool is_end, void *opcional_data), void *opcional_data);
void uws_res_upgrade(int ssl, uws_res_t *res, void *data, const char *sec_web_socket_key, size_t sec_web_socket_key_length, const char *sec_web_socket_protocol, size_t sec_web_socket_protocol_length, const char *sec_web_socket_extensions, size_t sec_web_socket_extensions_length, uws_socket_context_t *ws);


bool uws_req_is_ancient(uws_req_t *res);
bool uws_req_get_yield(uws_req_t *res);
void uws_req_set_field(uws_req_t *res, bool yield);
size_t uws_req_get_url(uws_req_t *res, const char **dest);
size_t uws_req_get_method(uws_req_t *res, const char **dest);
size_t uws_req_get_header(uws_req_t *res, const char *lower_case_header, size_t lower_case_header_length, const char **dest);
size_t uws_req_get_query(uws_req_t *res, const char *key, size_t key_length, const char **dest);
size_t uws_req_get_parameter(uws_req_t *res, unsigned short index, const char **dest);
""")

library_path = os.path.join(os.path.dirname(__file__), "libuwebsockets.so")

lib = ffi.dlopen(library_path)

@ffi.callback("void(uws_res_t *, uws_req_t *, void *)")
def uws_generic_method_handler(res, req, user_data):
    if not user_data == ffi.NULL:
        (handler, app) = ffi.from_handle(user_data)
        response = AppResponse(res, app.loop, False)
        request = AppRequest(req)
        try:
            if inspect.iscoroutinefunction(handler):
                response.grab_aborted_handler()
                app.run_async(handler(response, request), response)
            else:
                handler(response, request)
        except Exception as err:
            response.grab_aborted_handler()
            app.trigger_error(err, response, request)

@ffi.callback("void(uws_res_t *, uws_req_t *, void *)")
def uws_generic_ssl_method_handler(res, req, user_data):
    if not user_data == ffi.NULL:
        (handler, app) = ffi.from_handle(user_data)
        response = AppResponse(res, app.loop, True)
        request = AppRequest(req)
        try:
            if inspect.iscoroutinefunction(handler):
                response.grab_aborted_handler()
                app.run_async(handler(response, request), response)
            else:
                handler(response, request)
        except Exception as err:
            response.grab_aborted_handler()
            app.trigger_error(err, response, request)

@ffi.callback("void(struct us_listen_socket_t *, uws_app_listen_config_t, void *)")
def uws_generic_listen_handler(listen_socket, config, user_data):
    if listen_socket == ffi.NULL:
        raise RuntimeError("Failed to listen on port %d" % int(config.port))
    

    if not user_data == ffi.NULL:
        app = ffi.from_handle(user_data)
        config.port = lib.us_socket_local_port(app.SSL, listen_socket)
        if hasattr(app, "_listen_handler") and hasattr(app._listen_handler, '__call__'):
            app.socket = listen_socket
            app._listen_handler(None if config == ffi.NULL else AppListenOptions(port=int(config.port),host=None if config.host == ffi.NULL else ffi.string(config.host).decode("utf-8"), options=int(config.options)))

@ffi.callback("void(uws_res_t *, void*)")
def uws_generic_abord_handler(response, user_data):
    if not user_data == ffi.NULL:
        res = ffi.from_handle(user_data)
        res.aborted = True
        res.trigger_aborted()

class AppRequest:
    def __init__(self, request):
        self.req = request
    def get_url(self):
        buffer = ffi.new("char**")
        length = lib.uws_req_get_url(self.req, buffer)   
        buffer_address = ffi.addressof(buffer, 0)[0]
        if buffer_address == ffi.NULL: 
            return None
        return ffi.unpack(buffer_address, length)
    def get_method(self):
        buffer = ffi.new("char**")
        length = lib.uws_req_get_method(self.req, buffer)   
        buffer_address = ffi.addressof(buffer, 0)[0]
        if buffer_address == ffi.NULL: 
            return None
        return ffi.unpack(buffer_address, length)
    def get_header(self, lower_case_header):
        buffer = ffi.new("char**")
        data = lower_case_header.encode("utf-8")
        length = lib.uws_req_get_header(self.req, data, len(data), buffer)   
        buffer_address = ffi.addressof(buffer, 0)[0]
        if buffer_address == ffi.NULL: 
            return None
        return ffi.unpack(buffer_address, length)
    def get_query(self, key):
        buffer = ffi.new("char**")
        data = key.encode("utf-8")
        length = lib.uws_req_get_query(self.req, data, len(data), buffer)   
        buffer_address = ffi.addressof(buffer, 0)[0]
        if buffer_address == ffi.NULL: 
            return None
        return ffi.unpack(buffer_address, length)
    def get_parameter(self, index):
        buffer = ffi.new("char**")
        length = lib.uws_req_get_parameter(self.req, ffi.cast("unsigned short", index), buffer)   
        buffer_address = ffi.addressof(buffer, 0)[0]
        if buffer_address == ffi.NULL: 
            return None
        return ffi.unpack(buffer_address, length)
    def set_yield(self, has_yield):
        lib.uws_req_set_field(self.req, 1 if has_yield else 0)
    def get_yield(self):
        return bool(lib.uws_req_get_yield(self.req))
    def is_ancient(self):
        return bool(lib.uws_req_is_ancient(self.req))

class AppResponse:
    def __init__(self, response, loop, is_ssl):
        self.res = response
        self.SSL = ffi.cast("int", 1 if is_ssl else 0)
        self.aborted = False
        self._ptr = ffi.NULL
        self.loop = loop

    def run_async(self, task):
        self.grab_aborted_handler()
        return self.loop.run_async(task, self)

    def grab_aborted_handler(self):
        #only needed if is async
        if self._ptr == ffi.NULL:
            self._ptr = ffi.new_handle(self)
            lib.uws_res_on_aborted(self.SSL, self.res, uws_generic_abord_handler, self._ptr)
    
    def end(self, message, end_connection=False):
        if not self.aborted:
            if isinstance(message, str):
                data = message.encode("utf-8")
            elif isinstance(message, bytes):
                data = message
            else:
                self.write_header("Content-Type", "application/json")
                data = json.dumps(message).encode("utf-8")
            lib.uws_res_end(self.SSL, self.res, data, len(data), 1 if end_connection else 0)
        return self

    def pause(self):
        if not self.aborted:
            lib.uws_res_pause(self.SSL, self.res)
        return self

    def resume(self):
        if not self.aborted:
            lib.uws_res_resume(self.SSL, self.res)
        return self

    def write_continue(self):
        if not self.aborted:
            lib.uws_res_write_continue(self.SSL, self.res)
        return self

    def write_status(self, status_or_status_text):
        if not self.aborted:
            if isinstance(status_or_status_text, int):
                try:
                    data = status_codes[status_or_status_text].encode("utf-8")
                except: #invalid status
                    raise RuntimeError("\"%d\" Is not an valid Status Code" % status_or_status_text) 
            elif isinstance(status_text, str):
                data = status_text.encode("utf-8")
            elif isinstance(status_text, bytes):
                data = status_text
            else:
                data = json.dumps(status_text).encode("utf-8")

            lib.uws_res_write_status(self.SSL, self.res, data, len(data))
        return self

    def write_header(self, key, value):
        if not self.aborted:
            key_data = key.encode("utf-8")
            if isinstance(value, int):
                lib.uws_res_write_header_int(self.SSL, self.res, key_data, len(key_data),  ffi.cast("uint64_t", value))
            elif isinstance(value, str):
                value_data = value.encode("utf-8")
            elif isinstance(value, bytes):
                value_data = value
            else:
                value_data = json.dumps(value).encode("utf-8")
            lib.uws_res_write_header(self.SSL, self.res, key_data, len(key_data),  value_data, len(value_data))
        return self

    def end_without_body(self):
        if not self.aborted:
            lib.uws_res_end_without_body(self.SSL, self.res)
        return self

    def write(self, message):
        if not self.aborted:
            if isinstance(message, str):
                data = message.encode("utf-8")
            elif isinstance(message, bytes):
                data = message
            else:
                data = json.dumps(message).encode("utf-8")
            lib.uws_res_write(self.SSL, self.res, data, len(data))
        return self

    def get_write_offset(self, message):
        if not self.aborted:
            if isinstance(message, str):
                data = message.encode("utf-8")
            elif isinstance(message, bytes):
                data = message
            else:
                data = json.dumps(message).encode("utf-8")
            return int(lib.uws_res_get_write_offset(self.SSL, self.res, data, len(data)))
        return 0

    def has_responded(self):
        if not self.aborted:
            return False
        return bool(lib.uws_res_has_responded(self.SSL, self.res, data, len(data)))

    def trigger_aborted(self):
        if hasattr(self, "_aborted_handler") and hasattr(self._aborted_handler, '__call__'):
           self._aborted_handler()
        return self

    def on_aborted(self, handler):
        if hasattr(handler, '__call__'):
           self.grab_aborted_handler()
           self._aborted_handler = handler
        return self

    def __del__(self):
        self.res = ffi.NULL
        self._ptr = ffi.NULL
# void uws_res_on_data(int ssl, uws_res_t *res, void (*handler)(uws_res_t *res, const char *chunk, size_t chunk_length, bool is_end, void *opcional_data), void *opcional_data);
# void uws_res_upgrade(int ssl, uws_res_t *res, void *data, const char *sec_web_socket_key, size_t sec_web_socket_key_length, const char *sec_web_socket_protocol, size_t sec_web_socket_protocol_length, const char *sec_web_socket_extensions, size_t sec_web_socket_extensions_length, uws_socket_context_t *ws);
# void uws_res_on_writable(int ssl, uws_res_t *res, bool (*handler)(uws_res_t *res, uintmax_t, void *opcional_data), void *user_data);


class App:
    def __init__(self, options=None):
        socket_options_ptr = ffi.new("struct us_socket_context_options_t *")
        socket_options = socket_options_ptr[0]
        self.options = options
        if options != None:
            self.is_ssl = True
            self.SSL = ffi.cast("int", 1)
            socket_options.key_file_name = ffi.NULL if options.key_file_name == None else ffi.new("char[]", options.key_file_name.encode("utf-8"))
            socket_options.key_file_name = ffi.NULL if options.key_file_name == None else ffi.new("char[]", options.key_file_name.encode("utf-8"))
            socket_options.cert_file_name = ffi.NULL if options.cert_file_name == None else ffi.new("char[]", options.cert_file_name.encode("utf-8"))
            socket_options.passphrase = ffi.NULL if options.passphrase == None else ffi.new("char[]", options.passphrase.encode("utf-8"))
            socket_options.dh_params_file_name = ffi.NULL if options.dh_params_file_name == None else ffi.new("char[]", options.dh_params_file_name.encode("utf-8"))
            socket_options.ca_file_name = ffi.NULL if options.ca_file_name == None else ffi.new("char[]", options.ca_file_name.encode("utf-8"))
            socket_options.ssl_ciphers = ffi.NULL if options.ssl_ciphers == None else ffi.new("char[]", options.ssl_ciphers.encode("utf-8"))
            socket_options.ssl_prefer_low_memory_usage = ffi.cast("int", options.ssl_prefer_low_memory_usage)
        else:
            self.is_ssl = False
            self.SSL = ffi.cast("int", 0)
        self.app = lib.uws_create_app(self.SSL, socket_options)
        self._ptr = ffi.new_handle(self)
        if bool(lib.uws_constructor_failed(self.SSL, self.app)):
            raise RuntimeError("Failed to create connection") 
        self.handlers = []
        self.loop = Loop(lambda loop, context, response: self.trigger_error(context, response, None))
        self.error_handler = None

    def get(self, path, handler):
        user_data = ffi.new_handle((handler, self))
        self.handlers.append(user_data) #Keep alive handler
        lib.uws_app_get(self.SSL, self.app, path.encode("utf-8"), uws_generic_ssl_method_handler if self.is_ssl else uws_generic_method_handler, user_data)
        return self
    def post(self, path, handler):
        user_data = ffi.new_handle((handler, self))
        self.handlers.append(user_data) #Keep alive handler
        lib.uws_app_post(self.SSL, self.app, path.encode("utf-8"), uws_generic_ssl_method_handler if self.is_ssl else uws_generic_method_handler, user_data)
        return self
    def options(self, path, handler):
        user_data = ffi.new_handle((handler, self))
        self.handlers.append(user_data) #Keep alive handler
        lib.uws_app_options(self.SSL, self.app, path.encode("utf-8"), uws_generic_ssl_method_handler if self.is_ssl else uws_generic_method_handler, user_data)
        return self
    def delete(self, path, handler):
        user_data = ffi.new_handle((handler, self))
        self.handlers.append(user_data) #Keep alive handler
        lib.uws_app_delete(self.SSL, self.app, path.encode("utf-8"), uws_generic_ssl_method_handler if self.is_ssl else uws_generic_method_handler, user_data)
        return self
    def patch(self, path, handler):
        user_data = ffi.new_handle((handler, self))
        self.handlers.append(user_data) #Keep alive handler
        lib.uws_app_patch(self.SSL, self.app, path.encode("utf-8"), uws_generic_ssl_method_handler if self.is_ssl else uws_generic_method_handler, user_data)
        return self
    def put(self, path, handler):
        user_data = ffi.new_handle((handler, self))
        self.handlers.append(user_data) #Keep alive handler
        lib.uws_app_put(self.SSL, self.app, path.encode("utf-8"), uws_generic_ssl_method_handler if self.is_ssl else uws_generic_method_handler, user_data)
        return self
    def head(self, path, handler):
        user_data = ffi.new_handle((handler, self))
        self.handlers.append(user_data) #Keep alive handler
        lib.uws_app_head(self.SSL, self.app, path.encode("utf-8"), uws_generic_ssl_method_handler if self.is_ssl else uws_generic_method_handler, user_data)
        return self
    def connect(self, path, handler):
        user_data = ffi.new_handle((handler, self))
        self.handlers.append(user_data) #Keep alive handler
        lib.uws_app_connect(self.SSL, self.app, path.encode("utf-8"), uws_generic_ssl_method_handler if self.is_ssl else uws_generic_method_handler, user_data)
        return self
    def trace(self, path, handler):
        user_data = ffi.new_handle((handler, self))
        self.handlers.append(user_data) #Keep alive handler
        lib.uws_app_trace(self.SSL, self.app, path.encode("utf-8"), uws_generic_ssl_method_handler if self.is_ssl else uws_generic_method_handler, user_data)
        return self
    def any(self, path, handler):
        user_data = ffi.new_handle((handler, self))
        self.handlers.append(user_data) #Keep alive handler
        lib.uws_app_any(self.SSL, self.app, path.encode("utf-8"), uws_generic_ssl_method_handler if self.is_ssl else uws_generic_method_handler, user_data)
        return self

    def listen(self, port_or_options, handler=None):
        self._listen_handler = handler
        if isinstance(port_or_options, int): 
            lib.uws_app_listen(self.SSL, self.app, ffi.cast("int", port_or_options), uws_generic_listen_handler, self._ptr)
        else:
            native_options = ffi.new("uws_app_listen_config_t *")
            options = native_options[0]
            options.port = ffi.cast("int", port_or_options.port)
            options.host = ffi.NULL if port_or_options.host == None else ffi.new("char[]", port_or_options.host.encode("utf-8"))
            options.options = ffi.cast("int", port_or_options.options)
            self.native_options_listen = native_options #Keep alive native_options
            lib.uws_app_listen_with_config(self.SSL, self.app, options, uws_generic_listen_handler, self._ptr)

        return self

    def get_loop():
        return self.loop.loop
        
    def run_async(self, task, response=None):
        return self.loop.run_async(task, response)

    def run(self):
        self.loop.start()
        lib.uws_app_run(self.SSL, self.app)
        self.loop.stop()
        return self
        
    def close(self):
        if hasattr(self, "socket"):
            if not self.socket == ffi.NULL:
                lib.us_listen_socket_close(self.SSL, self.socket)
        return self

    def set_error_handler(self, handler):
        if hasattr(handler, '__call__'):
            self.error_handler = handler 
        else:
            self.error_handler = None

    def trigger_error(self, error, response, request):
        if self.error_handler == None:
            try:
                print("Uncaught Exception: %s" % str(error)) #just log in console the error to call attention
                response.write_status(500).end("Internal Error")
            finally:
                return
        else:
            try:
                if inspect.iscoroutinefunction(self.error_handler ):
                    self.run_async(self.error_handler(error, response, request), response)
                else:
                    self.error_handler(error, response, request)
            except Exception as error:
                try:
                    #Error handler got an error :D
                    print("Uncaught Exception: %s" % str(error)) #just log in console the error to call attention
                    response.write_status(500).end("Internal Error")
                finally:
                   pass

    
    def __del__(self):
        lib.uws_app_destroy(self.SSL, self.app)


class AppListenOptions:
    def __init__(self, port=0, host=None, options=0):
        if not isinstance(port, int): raise RuntimeError("port must be an int") 
        if host != None and not isinstance(host, str): raise RuntimeError("host must be an String or None") 
        if not isinstance(options, int): raise RuntimeError("options must be an int") 
        self.port = port
        self.host = host
        self.options = options
        
class AppOptions:
    def __init__(self, key_file_name=None, cert_file_name=None, passphrase=None, dh_params_file_name=None, ca_file_name=None, ssl_ciphers=None, ssl_prefer_low_memory_usage=0):
        if key_file_name != None and not isinstance(key_file_name, str): raise RuntimeError("key_file_name must be an String or None") 
        if cert_file_name != None and not isinstance(cert_file_name, str): raise RuntimeError("cert_file_name must be an String or None") 
        if passphrase != None and not isinstance(passphrase, str): raise RuntimeError("passphrase must be an String or None") 
        if dh_params_file_name != None and not isinstance(dh_params_file_name, str): raise RuntimeError("dh_params_file_name must be an String or None") 
        if ca_file_name != None and not isinstance(ca_file_name, str): raise RuntimeError("ca_file_name must be an String or None") 
        if ssl_ciphers != None and not isinstance(ssl_ciphers, str): raise RuntimeError("ssl_ciphers must be an String or None") 
        if not isinstance(ssl_prefer_low_memory_usage, int): raise RuntimeError("ssl_prefer_low_memory_usage must be an int") 

        self.key_file_name = key_file_name
        self.cert_file_name = cert_file_name
        self.passphrase = passphrase
        self.dh_params_file_name = dh_params_file_name
        self.ca_file_name = ca_file_name
        self.ssl_ciphers = ssl_ciphers
        self.ssl_prefer_low_memory_usage = ssl_prefer_low_memory_usage

