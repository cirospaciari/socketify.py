import os
import inspect
from socketify import App
from .asgi import ws_close, ws_upgrade, ws_open, ws_message
from io import BytesIO
from .native import lib, ffi


@ffi.callback("void(uws_res_t*, const char*, size_t, bool, void*)")
def wsgi_on_data_handler(res, chunk, chunk_length, is_end, user_data):
    data_response = ffi.from_handle(user_data)
    if chunk != ffi.NULL:
        data_response.buffer.write(ffi.unpack(chunk, chunk_length))
    if bool(is_end):
        lib.uws_res_cork(
            data_response.app.server.SSL,
            res,
            wsgi_corked_response_start_handler,
            data_response._ptr,
        )


class WSGIDataResponse:
    def __init__(self, app, environ, start_response, aborted, buffer, on_data):
        self.buffer = buffer
        self.aborted = aborted
        self._ptr = ffi.new_handle(self)
        self.on_data = on_data
        self.environ = environ
        self.app = app
        self.start_response = start_response

@ffi.callback("void(uws_res_t*, void*)")
def wsgi_corked_response_start_handler(res, user_data):
    data_response = ffi.from_handle(user_data)
    data_response.on_data(data_response, res)


@ffi.callback("void(int, uws_res_t*, socketify_asgi_data request, void*, bool*)")
def wsgi(ssl, response, info, user_data, aborted):
    app = ffi.from_handle(user_data)
    # reusing the dict is slower than cloning because we need to clear HTTP headers
    environ = dict(app.BASIC_ENVIRON)

    environ["REQUEST_METHOD"] = ffi.unpack(info.method, info.method_size).decode("utf8")
    environ["PATH_INFO"] = ffi.unpack(info.url, info.url_size).decode("utf8")
    environ["QUERY_STRING"] = ffi.unpack(
        info.query_string, info.query_string_size
    ).decode("utf8")
    if info.remote_address != ffi.NULL:
        environ["REMOTE_ADDR"] = ffi.unpack(
            info.remote_address, info.remote_address_size
        ).decode("utf8")
    else:
        environ["REMOTE_ADDR"] = "127.0.0.1"

    next_header = info.header_list
    while next_header != ffi.NULL:
        header = next_header[0]
        name = ffi.unpack(header.name, header.name_size).decode("utf8")
        value = ffi.unpack(header.value, header.value_size).decode("utf8")
        # this conversion should be optimized in future
        environ[f"HTTP_{name.replace('-', '_').upper()}"] = value
        next_header = ffi.cast("socketify_header*", next_header.next)

    def start_response(status, headers):
        if isinstance(status, str):
            data = status.encode("utf-8")
            lib.uws_res_write_status(ssl, response, data, len(data))
        elif isinstance(status, bytes):
            lib.uws_res_write_status(ssl, response, status, len(status))
            
        for (key, value) in headers:
            if isinstance(key, str):
            # this is faster than using .lower()
                if (
                    key == "content-length"
                    or key == "Content-Length"
                    or key == "Transfer-Encoding"
                    or key == "transfer-encoding"
                ):
                    continue  # auto
                key_data = key.encode("utf-8")
            elif isinstance(key, bytes):
                # this is faster than using .lower()
                if (
                    key == b"content-length"
                    or key == b"Content-Length"
                    or key == b"Transfer-Encoding"
                    or key == b"transfer-encoding"
                ):
                    continue  # auto
                key_data = key

            
            if isinstance(value, str):
                value_data = value.encode("utf-8")
            elif isinstance(value, bytes):
                value_data = value
            elif isinstance(value, int):
                lib.uws_res_write_header_int(
                    ssl,
                    response,
                    key_data,
                    len(key_data),
                    ffi.cast("uint64_t", value),
                )
                continue
            
            lib.uws_res_write_header(
                ssl, response, key_data, len(key_data), value_data, len(value_data)
            )
        lib.uws_res_write_header(
            ssl, response, b'Server', 6, b'socketify.py', 12
        )

    # check for body
    if bool(info.has_content):
        WSGI_INPUT = BytesIO()
        environ["wsgi.input"] = WSGI_INPUT

        def on_data(data_response, response):
            if bool(data_response.aborted[0]):
                return

            ssl = data_response.app.server.SSL
            app_iter = data_response.app.app(
                data_response.environ, data_response.start_response
            )
            try:
                for data in app_iter:
                    if isinstance(data, bytes):
                        lib.uws_res_write(ssl, response, data, len(data))
                    elif isinstance(data, str):
                        data = data.encode("utf-8")
                        lib.uws_res_write(ssl, response, data, len(data))
                    
                    
            finally:
                if hasattr(app_iter, "close"):
                    app_iter.close()
            lib.uws_res_end_without_body(ssl, response, 0)

        data_response = WSGIDataResponse(
            app, environ, start_response, aborted, WSGI_INPUT, on_data
        )

        lib.uws_res_on_data(ssl, response, wsgi_on_data_handler, data_response._ptr)
    else:
        environ["wsgi.input"] = None
        app_iter = app.app(environ, start_response)
        try:
            for data in app_iter:
                if isinstance(data, bytes):
                    lib.uws_res_write(ssl, response, data, len(data))
                elif isinstance(data, str):
                    data = data.encode("utf-8")
                    lib.uws_res_write(ssl, response, data, len(data))
        finally:
            if hasattr(app_iter, "close"):
                app_iter.close()
        lib.uws_res_end_without_body(ssl, response, 0)


class _WSGI:
    def __init__(self, app, options=None, websocket=None, websocket_options=None):
        self.server = App(options)
        self.SERVER_HOST = None
        self.SERVER_PORT = None
        self.SERVER_WS_SCHEME = "wss" if self.server.options else "ws"
        self.app = app
        self.BASIC_ENVIRON = dict(os.environ)
        self.ws_compression = False

        self._ptr = ffi.new_handle(self)
        self.asgi_http_info = lib.socketify_add_asgi_http_handler(
            self.server.SSL, self.server.app, wsgi, self._ptr
        )
        self.asgi_ws_info = None
        if isinstance(websocket, dict):  # serve websocket as socketify.py
            if websocket_options:
                websocket.update(websocket_options)

            self.server.ws("/*", websocket)
        elif inspect.iscoroutine(websocket):
            # detect ASGI to use as WebSocket as mixed protocol
            native_options = ffi.new("uws_socket_behavior_t *")
            native_behavior = native_options[0]

            if not websocket_options:
                websocket_options = {}

            self.ws_compression = websocket_options.get("compression", False)

            native_behavior.maxPayloadLength = ffi.cast(
                "unsigned int",
                int(websocket_options.get("max_payload_length", 16777216)),
            )
            native_behavior.idleTimeout = ffi.cast(
                "unsigned short",
                int(websocket_options.get("idle_timeout", 20)),
            )
            native_behavior.maxBackpressure = ffi.cast(
                "unsigned int",
                int(websocket_options.get("max_backpressure", 16777216)),
            )
            native_behavior.compression = ffi.cast(
                "uws_compress_options_t", int(self.ws_compression)
            )
            native_behavior.maxLifetime = ffi.cast(
                "unsigned short", int(websocket_options.get("max_lifetime", 0))
            )
            native_behavior.closeOnBackpressureLimit = ffi.cast(
                "int",
                int(websocket_options.get("close_on_backpressure_limit", 0)),
            )
            native_behavior.resetIdleTimeoutOnSend = ffi.cast(
                "int", bool(websocket_options.get("reset_idle_timeout_on_send", True))
            )
            native_behavior.sendPingsAutomatically = ffi.cast(
                "int", bool(websocket_options.get("send_pings_automatically", True))
            )

            native_behavior.upgrade = ffi.NULL  # will be set first on C++

            native_behavior.open = ws_open
            native_behavior.message = ws_message
            native_behavior.ping = ffi.NULL
            native_behavior.pong = ffi.NULL
            native_behavior.close = ws_close

            self.asgi_ws_info = lib.socketify_add_asgi_ws_handler(
                self.server.SSL, self.server.app, native_behavior, ws_upgrade, self._ptr
            )

    def listen(self, port_or_options, handler=None):
        self.SERVER_PORT = (
            port_or_options
            if isinstance(port_or_options, int)
            else port_or_options.port
        )
        self.SERVER_HOST = (
            "0.0.0.0" if isinstance(port_or_options, int) else port_or_options.host
        )
        self.BASIC_ENVIRON.update(
            {
                "GATEWAY_INTERFACE": "CGI/1.1",
                "SERVER_PORT": str(self.SERVER_PORT),
                "SERVER_SOFTWARE": "WSGIServer/0.2",
                "wsgi.input": None,
                "wsgi.errors": None,
                "wsgi.version": (1, 0),
                "wsgi.run_once": False,
                "wsgi.url_scheme": "https" if self.server.options else "http",
                "wsgi.multithread": False,
                "wsgi.multiprocess": False,
                "wsgi.file_wrapper": None,  # No file wrapper support for now
                "SCRIPT_NAME": "",
                "SERVER_PROTOCOL": "HTTP/1.1",
                "REMOTE_HOST": "",
            }
        )
        self.server.listen(port_or_options, handler)
        return self

    def run(self):
        self.server.run()
        return self

    def __del__(self):
        if self.asgi_http_info:
            lib.socketify_destroy_asgi_app_info(self.asgi_http_info)
        if self.asgi_ws_info:
            lib.socketify_destroy_asgi_ws_app_info(self.asgi_ws_info)


# "Public" WSGI interface to allow easy forks/workers
class WSGI:
    def __init__(self, app, options=None, websocket=None, websocket_options=None):
        self.app = app
        self.options = options
        self.websocket = websocket
        self.websocket_options = websocket_options
        self.listen_options = None

    def listen(self, port_or_options, handler=None):
        self.listen_options = (port_or_options, handler)
        return self

    def run(self, workers=1):
        def run_app():
            server = _WSGI(
                self.app, self.options, self.websocket, self.websocket_options
            )
            if self.listen_options:
                (port_or_options, handler) = self.listen_options
                server.listen(port_or_options, handler)
            server.run()

        def create_fork():
            n = os.fork()
            # n greater than 0 means parent process
            if not n > 0:
                run_app()

        # fork limiting the cpu count - 1
        for i in range(1, workers):
            create_fork()

        run_app()  # run app on the main process too :)
        return self
