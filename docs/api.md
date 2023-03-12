## App
```python

class App:
    def __init__(self, options=None, request_response_factory_max_items=0, websocket_factory_max_items=0, task_factory_max_items=100_000, lifespan=True):

    def on_start(self, method: callable):
    def on_shutdown(self, method: callable):
    def on_error(self, method: callable):    
    def router(self, prefix: str="", *middlewares):
    def register(self, extension):
    def template(self, template_engine):
    def json_serializer(self, json_serializer):
    def static(self, route, directory):
    def get(self, path, handler):
    def post(self, path, handler):
    def options(self, path, handler):
    def delete(self, path, handler):
    def patch(self, path, handler):
    def put(self, path, handler):
    def head(self, path, handler):
    def connect(self, path, handler):
    def trace(self, path, handler):
    def any(self, path, handler):
    def get_native_handle(self):
    def num_subscribers(self, topic):
    def publish(self, topic, message, opcode=OpCode.BINARY, compress=False):
    def remove_server_name(self, hostname):
    def add_server_name(self, hostname, options=None):
    def missing_server_name(self, handler):
    def ws(self, path, behavior):
    def listen(self, port_or_options=None, handler=None):
    def run_async(self, task, response=None):
    def run(self):
    def close(self):
    def set_error_handler(self, handler):
    def __del__(self):

```

## Response
```python
class Response:
    def __init__(self, response, app):
    def cork(self, callback):
    def close(self):
    def set_cookie(self, name, value, options={}):
    def run_async(self, task):
    async def get_form_urlencoded(self, encoding="utf-8"):
    async def get_text(self, encoding="utf-8"):
    async def get_json(self):
    def send_chunk(self, buffer, total_size):
    def get_data(self):
    def grab_aborted_handler(self):
    def redirect(self, location, status_code=302):
    def write_offset(self, offset):
    def try_end(self, message, total_size, end_connection=False):
    def cork_end(self, message, end_connection=False):
    def render(self, *args, **kwargs):
    def get_remote_address_bytes(self):
    def get_remote_address(self):
    def get_proxied_remote_address_bytes(self):
    def get_proxied_remote_address(self):
    def cork_send(self, message: any, content_type: str = b'text/plain', status : str | bytes | int = b'200 OK', headers=None, end_connection=False):
    def send(self, message: any = b"", content_type: str = b'text/plain', status : str | bytes | int = b'200 OK', headers=None, end_connection=False):
    def end(self, message, end_connection=False):
    def pause(self):
    def resume(self):
    def write_continue(self):
    def write_status(self, status_or_status_text):
    def write_header(self, key, value):
    def end_without_body(self, end_connection=False):
    def write(self, message):
    def get_write_offset(self):
    def has_responded(self):
    def on_aborted(self, handler):
    def on_data(self, handler):
    def upgrade(
        self,
        sec_web_socket_key,
        sec_web_socket_protocol,
        sec_web_socket_extensions,
        socket_context,
        user_data=None,
    ):
    def on_writable(self, handler):
    def get_native_handle(self):
    def __del__(self):
```

## Request
```python
class Request:
    def __init__(self, request, app):
    def get_cookie(self, name):
    def get_url(self):
    def get_full_url(self):
    def get_method(self):
    def for_each_header(self, handler):
    def get_headers(self):
    def get_header(self, lower_case_header):
    def get_queries(self):
    def get_query(self, key):
    def get_parameters(self):
    def get_parameter(self, index):
    def preserve(self):
    def set_yield(self, has_yield):
    def get_yield(self):
    def is_ancient(self):
    def __del__(self):
```
## AppListenOptions
```python
class AppListenOptions:
    port: int = 0
    host: str = None
    options: int = 0
    domain: str = None
```
## AppOptions
```python
class AppOptions:
    key_file_name: str = None,
    cert_file_name: str = None,
    passphrase: str = None,
    dh_params_file_name: str = None,
    ca_file_name: str = None,
    ssl_ciphers: str = None,
    ssl_prefer_low_memory_usage: int = 0
```

## WebSockets
```python

class WebSocket:
    def __init__(self, websocket, app):

    # uuid for socket data, used to free data after socket closes
    def get_user_data_uuid(self):
    def get_user_data(self):
    # clone the current instance to preserve it (you need to watch for closed connections when using it)
    def clone(self):
    def get_buffered_amount(self):
    def subscribe(self, topic):
    def unsubscribe(self, topic):
    def is_subscribed(self, topic):
    def publish(self, topic, message, opcode=OpCode.BINARY, compress=False):
    def get_topics(self):
    def for_each_topic(self, handler):
    def get_remote_address_bytes(self):
    def get_remote_address(self):
    def send_fragment(self, message, compress=False):
    def send_last_fragment(self, message, compress=False):
    def send_first_fragment(self, message, opcode=OpCode.BINARY, compress=False):
    def cork_send(self, message, opcode=OpCode.BINARY, compress=False, fin=True):
    def send(self, message, opcode=OpCode.BINARY, compress=False, fin=True):
    def cork_end(self, code=0, message=None):
    def end(self, code=0, message=None):
    def close(self):
    def cork(self, callback):
    def __del__(self):
```

## Enums
```python
# Compressor mode is 8 lowest bits where HIGH4(windowBits), LOW4(memLevel).
# Decompressor mode is 8 highest bits LOW4(windowBits).
# If compressor or decompressor bits are 1, then they are shared.
# If everything is just simply 0, then everything is disabled.
class CompressOptions(IntEnum):
    # Disabled, shared, shared are "special" values
    DISABLED = lib.DISABLED
    SHARED_COMPRESSOR = lib.SHARED_COMPRESSOR
    SHARED_DECOMPRESSOR = lib.SHARED_DECOMPRESSOR
    # Highest 4 bits describe decompressor
    DEDICATED_DECOMPRESSOR_32KB = lib.DEDICATED_DECOMPRESSOR_32KB
    DEDICATED_DECOMPRESSOR_16KB = lib.DEDICATED_DECOMPRESSOR_16KB
    DEDICATED_DECOMPRESSOR_8KB = lib.DEDICATED_DECOMPRESSOR_8KB
    DEDICATED_DECOMPRESSOR_4KB = lib.DEDICATED_DECOMPRESSOR_4KB
    DEDICATED_DECOMPRESSOR_2KB = lib.DEDICATED_DECOMPRESSOR_2KB
    DEDICATED_DECOMPRESSOR_1KB = lib.DEDICATED_DECOMPRESSOR_1KB
    DEDICATED_DECOMPRESSOR_512B = lib.DEDICATED_DECOMPRESSOR_512B
    # Same as 32kb
    DEDICATED_DECOMPRESSOR = (lib.DEDICATED_DECOMPRESSOR,)

    # Lowest 8 bit describe compressor
    DEDICATED_COMPRESSOR_3KB = lib.DEDICATED_COMPRESSOR_3KB
    DEDICATED_COMPRESSOR_4KB = lib.DEDICATED_COMPRESSOR_4KB
    DEDICATED_COMPRESSOR_8KB = lib.DEDICATED_COMPRESSOR_8KB
    DEDICATED_COMPRESSOR_16KB = lib.DEDICATED_COMPRESSOR_16KB
    DEDICATED_COMPRESSOR_32KB = lib.DEDICATED_COMPRESSOR_32KB
    DEDICATED_COMPRESSOR_64KB = lib.DEDICATED_COMPRESSOR_64KB
    DEDICATED_COMPRESSOR_128KB = lib.DEDICATED_COMPRESSOR_128KB
    DEDICATED_COMPRESSOR_256KB = lib.DEDICATED_COMPRESSOR_256KB
    # Same as 256kb
    DEDICATED_COMPRESSOR = lib.DEDICATED_COMPRESSOR


class OpCode(IntEnum):
    CONTINUATION = 0
    TEXT = 1
    BINARY = 2
    CLOSE = 8
    PING = 9
    PONG = 10


class SendStatus(IntEnum):
    BACKPRESSURE = 0
    SUCCESS = 1
    DROPPED = 2
```


## Helpers
```python
async def sendfile(res, req, filename)
def middleware(*functions):

class MiddlewareRouter:
    def __init__(self, app, *middlewares):
    def get(self, path, handler):
    def post(self, path, handler):
    def options(self, path, handler):
    def delete(self, path, handler):
    def patch(self, path, handler):
    def put(self, path, handler):
    def head(self, path, handler):
    def connect(self, path, handler):
    def trace(self, path, handler):
    def any(self, path, handler):
```