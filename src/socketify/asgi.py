from socketify import App, OpCode, Loop
from queue import SimpleQueue
from .native import lib, ffi
from .tasks import create_task, create_task_with_factory
import os
import platform
import sys 
import logging
import uuid
import asyncio
is_pypy = platform.python_implementation() == "PyPy"
async def task_wrapper(task):
    try:
        return await task
    except Exception as error:
        try:
            # just log in console the error to call attention
            logging.error("Uncaught Exception: %s" % str(error))
        finally:
            return None

EMPTY_RESPONSE = {"type": "http.request", "body": b"", "more_body": False}


@ffi.callback("void(uws_websocket_t*, const char*, size_t, uws_opcode_t, void*)")
def ws_message(ws, message, length, opcode, user_data):
    socket_data = ffi.from_handle(user_data)
    message = None if message == ffi.NULL else ffi.unpack(message, length)
    if opcode == OpCode.TEXT:
        message = message.decode("utf8")

    socket_data.message(ws, message, OpCode(opcode))
    

@ffi.callback("void(uws_websocket_t*, int, const char*, size_t, void*)")
def ws_close(ws, code, message, length, user_data):
    socket_data = ffi.from_handle(user_data)
    message = None if message == ffi.NULL else ffi.unpack(message, length)
    socket_data.disconnect(code, message)


@ffi.callback("void(uws_websocket_t*, void*)")
def ws_open(ws, user_data):
    socket_data = ffi.from_handle(user_data)
    socket_data.open(ws)


@ffi.callback(
    "void(int, uws_res_t*, socketify_asgi_ws_data, uws_socket_context_t* socket, void*, bool*)"
)
def ws_upgrade(ssl, response, info, socket_context, user_data, aborted):
    app = ffi.from_handle(user_data)
    headers = []
    next_header = info.header_list
    while next_header != ffi.NULL:
        header = next_header[0]
        headers.append(
            (
                ffi.unpack(header.name, header.name_size),
                ffi.unpack(header.value, header.value_size),
            )
        )
        next_header = ffi.cast("socketify_header*", next_header.next)

    url = ffi.unpack(info.url, info.url_size)

    if info.key == ffi.NULL:
        key = None
    else:
        key = ffi.unpack(info.key, info.key_size).decode("utf8")

    if info.protocol == ffi.NULL:
        protocol = None
    else:
        protocol = ffi.unpack(info.protocol, info.protocol_size).decode("utf8")
    if info.extensions == ffi.NULL:
        extensions = None
    else:
        extensions = ffi.unpack(info.extensions, info.extensions_size).decode("utf8")
    compress = app.ws_compression
    ws = ASGIWebSocket(app.server.loop)
    
    scope = {
        "type": "websocket",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "server": (app.SERVER_HOST, app.SERVER_PORT),
        "client": (
            ffi.unpack(info.remote_address, info.remote_address_size).decode("utf8"),
            None,
        ),
        "scheme": app.SERVER_WS_SCHEME,
        "method": ffi.unpack(info.method, info.method_size).decode("utf8"),
        "root_path": "",
        "path": url.decode("utf8"),
        "raw_path": url,
        "query_string": ffi.unpack(info.query_string, info.query_string_size),
        "headers": headers,
        "subprotocols": [protocol] if protocol else [],
        "extensions": {
            "websocket.publish": True,
            "websocket.subscribe": True,
            "websocket.unsubscribe": True,
        },
    }

    async def send(options):
        if bool(aborted[0]):
            return False
        type = options["type"]
        if type == "websocket.send":
            data = options.get("bytes", None)
            if ws.ws:
                if data:
                    lib.socketify_ws_cork_send_with_options(
                        ssl,
                        ws.ws,
                        data,
                        len(data),
                        int(OpCode.BINARY),
                        int(compress),
                        1,
                    )
                else:
                    data = options.get("text", "").encode("utf8")
                    lib.socketify_ws_cork_send_with_options(
                        ssl, ws.ws, data, len(data), int(OpCode.TEXT), int(compress), 1
                    )
                return True
            return False
        if type == "websocket.accept":  # upgrade!
            res_headers = options.get("headers", None)
            if res_headers:
                cork_data = ffi.new_handle((ssl, res_headers))
                lib.uws_res_cork(
                    ssl, response, uws_asgi_corked_ws_accept_handler, cork_data
                )

            future = ws.accept()
            upgrade_protocol = options.get("subprotocol", protocol)

            if isinstance(key, str):
                sec_web_socket_key_data = key.encode("utf-8")
            elif isinstance(key, bytes):
                sec_web_socket_key_data = key
            else:
                sec_web_socket_key_data = b""

            if isinstance(upgrade_protocol, str):
                sec_web_socket_protocol_data = upgrade_protocol.encode("utf-8")
            elif isinstance(upgrade_protocol, bytes):
                sec_web_socket_protocol_data = upgrade_protocol
            else:
                sec_web_socket_protocol_data = b""

            if isinstance(extensions, str):
                sec_web_socket_extensions_data = extensions.encode("utf-8")
            elif isinstance(extensions, bytes):
                sec_web_socket_extensions_data = extensions
            else:
                sec_web_socket_extensions_data = b""
            _id = uuid.uuid4()
            
            app.server._socket_refs[_id] = ws
            def unregister():
                app.server._socket_refs.pop(_id, None)
            ws.unregister = unregister
            lib.uws_res_upgrade(
                ssl,
                response,
                ws._ptr,
                sec_web_socket_key_data,
                len(sec_web_socket_key_data),
                sec_web_socket_protocol_data,
                len(sec_web_socket_protocol_data),
                sec_web_socket_extensions_data,
                len(sec_web_socket_extensions_data),
                socket_context,
            )
            return await future
        if type == "websocket.close":  # code and reason?
            if ws.ws:
                lib.uws_ws_close(ssl, ws.ws)
            else:
                cork_data = ffi.new_handle(ssl)
                lib.uws_res_cork(ssl, response, uws_asgi_corked_403_handler, cork_data)
            return True
        if type == "websocket.publish":  # publish extension
            data = options.get("bytes", None)
            if data:
                app.server.publish(options.get("topic"), data, OpCode.BINARY, compress)
            else:
                app.server.publish(
                    options.get("topic"), options.get("text", ""), OpCode.TEXT, compress
                )
            return True
        if type == "websocket.subscribe":  # subscribe extension
            if ws.ws:
                topic = options.get("topic")
                if isinstance(topic, str):
                    data = topic.encode("utf-8")
                elif isinstance(topic, bytes):
                    data = topic
                else:
                    return False

                return bool(lib.uws_ws_subscribe(ssl, ws.ws, data, len(data)))
            else:
                cork_data = ffi.new_handle(ssl)
                lib.uws_res_cork(ssl, response, uws_asgi_corked_403_handler, cork_data)
            return True
        if type == "websocket.unsubscribe":  # unsubscribe extension
            if ws.ws:
                topic = options.get("topic")
                if isinstance(topic, str):
                    data = topic.encode("utf-8")
                elif isinstance(topic, bytes):
                    data = topic
                else:
                    return False

                return bool(lib.uws_ws_unsubscribe(ssl, ws.ws, data, len(data)))
            else:
                cork_data = ffi.new_handle(ssl)
                lib.uws_res_cork(ssl, response, uws_asgi_corked_403_handler, cork_data)
            return True
        return False

    app._run_task(app.app(scope, ws.receive, send))


@ffi.callback("void(uws_res_t*, const char*, size_t, bool, void*)")
def asgi_on_data_handler(res, chunk, chunk_length, is_end, user_data):
    data_response = ffi.from_handle(user_data)
    data_response.is_end = bool(is_end)
    more_body = not data_response.is_end
    result = {
        "type": "http.request",
        "body": b"" if chunk == ffi.NULL else ffi.unpack(chunk, chunk_length),
        "more_body": more_body,
    }
    data_response.queue.put(result, False)
    data_response.next_data_future.set_result(result)
    if more_body:
        data_response.next_data_future = data_response.loop.create_future()


class ASGIDataQueue:
    def __init__(self, loop):
        self.queue = SimpleQueue()
        self._ptr = ffi.new_handle(self)
        self.loop = loop
        self.is_end = False
        self.next_data_future = loop.create_future()


class ASGIWebSocket:
    def __init__(self, loop):
        self.loop = loop
        self.accept_future = None
        self.ws = None
        self._disconnected = False
        self.receive_queue = SimpleQueue()
        self.miss_receive_queue = SimpleQueue()
        self.miss_receive_queue.put({"type": "websocket.connect"}, False)
        self._code = None
        self._message = None
        self._ptr = ffi.new_handle(self)
        self.unregister = None

    def accept(self):
        self.accept_future = self.loop.create_future()
        return self.accept_future

    def open(self, ws):
        self.ws = ws
        if not self.accept_future.done():
            self.accept_future.set_result(True)

    def receive(self):
        future = self.loop.create_future()
        if not self.miss_receive_queue.empty():
            future.set_result(self.miss_receive_queue.get(False))
            return future
        if self._disconnected:
            future.set_result(
                {
                    "type": "websocket.disconnect",
                    "code": self._code,
                    "message": self._message,
                }
            )
            return future

        self.receive_queue.put(future, False)
        return future

    def disconnect(self, code, message):
        self.ws = None
        self._disconnected = True
        self._code = code
        self._message = message
        if not self.receive_queue.empty():
            future = self.receive_queue.get(False)
            future.set_result(
                {"type": "websocket.disconnect", "code": code, "message": message}
            )
        if self.unregister is not None:
            self.unregister()

    def message(self, ws, value, opcode):
        self.ws = ws
        if self.receive_queue.empty():
            if opcode == OpCode.TEXT:
                self.miss_receive_queue.put(
                    {"type": "websocket.receive", "text": value}, False
                )
            elif opcode == OpCode.BINARY:
                self.miss_receive_queue.put(
                    {"type": "websocket.receive", "bytes": value}, False
                )
            return True

        future = self.receive_queue.get(False)
        if opcode == OpCode.TEXT:
            future.set_result({"type": "websocket.receive", "text": value})
        elif opcode == OpCode.BINARY:
            future.set_result({"type": "websocket.receive", "bytes": value})


def write_header(ssl, res, key, value):
    if isinstance(key, bytes):
        # this is faster than using .lower()
        if (
            key == b"content-length"
            or key == b"Content-Length"
            or key == b"Transfer-Encoding"
            or key == b"transfer-encoding"
        ):
            return  # auto
        key_data = key
    elif isinstance(key, str):
        # this is faster than using .lower()
        if (
            key == "content-length"
            or key == "Content-Length"
            or key == "Transfer-Encoding"
            or key == "transfer-encoding"
        ):
            return  # auto
        key_data = key.encode("utf-8")

    if isinstance(value, bytes):
        value_data = value
    elif isinstance(value, str):
        value_data = value.encode("utf-8")
    elif isinstance(value, int):
        lib.uws_res_write_header_int(
            ssl,
            res,
            key_data,
            len(key_data),
            ffi.cast("uint64_t", value),
        )
    lib.uws_res_write_header(
        ssl, res, key_data, len(key_data), value_data, len(value_data)
    )


@ffi.callback("void(uws_res_t*, void*)")
def uws_asgi_corked_response_start_handler(res, user_data):
    (ssl, status, headers) = ffi.from_handle(user_data)
    if status != 200:
        lib.socketify_res_write_int_status(ssl, res, int(status))
    for name, value in headers:
        write_header(ssl, res, name, value)
    write_header(ssl, res, b"Server", b"socketify.py")


@ffi.callback("void(uws_res_t*, void*)")
def uws_asgi_corked_accept_handler(res, user_data):
    (ssl, status, headers) = ffi.from_handle(user_data)
    if status != 200:
        lib.socketify_res_write_int_status(ssl, res, int(status))
    for name, value in headers:
        write_header(ssl, res, name, value)
    write_header(ssl, res, b"Server", b"socketify.py")


@ffi.callback("void(uws_res_t*, void*)")
def uws_asgi_corked_ws_accept_handler(res, user_data):
    (ssl, headers) = ffi.from_handle(user_data)
    for name, value in headers:
        write_header(ssl, res, name, value)
    write_header(ssl, res, b"Server", b"socketify.py")


@ffi.callback("void(uws_res_t*, void*)")
def uws_asgi_corked_403_handler(res, user_data):
    ssl = ffi.from_handle(user_data)
    lib.socketify_res_write_int_status(ssl, res, int(403))
    lib.uws_res_end_without_body(ssl, res, 0)


@ffi.callback("void(int, uws_res_t*, socketify_asgi_data, void*, bool*)")
def asgi(ssl, response, info, user_data, aborted):
    app = ffi.from_handle(user_data)

    headers = []
    next_header = info.header_list
    while next_header != ffi.NULL:
        header = next_header[0]
        headers.append(
            (
                ffi.unpack(header.name, header.name_size),
                ffi.unpack(header.value, header.value_size),
            )
        )
        next_header = ffi.cast("socketify_header*", next_header.next)
    url = ffi.unpack(info.url, info.url_size)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "server": (app.SERVER_HOST, app.SERVER_PORT),
        "client": (
            ffi.unpack(info.remote_address, info.remote_address_size).decode("utf8"),
            None,
        ),
        "scheme": app.SERVER_SCHEME,
        "method": ffi.unpack(info.method, info.method_size).decode("utf8"),
        "root_path": "",
        "path": url.decode("utf8"),
        "raw_path": url,
        "query_string": ffi.unpack(info.query_string, info.query_string_size),
        "headers": headers,
    }
    if bool(info.has_content):
        data_queue = ASGIDataQueue(app.server.loop)
        lib.uws_res_on_data(ssl, response, asgi_on_data_handler, data_queue._ptr)
    else:
        data_queue = None

    async def receive():
        if bool(aborted[0]):
            return {"type": "http.disconnect"}
        if data_queue:
            if data_queue.queue.empty():
                if not data_queue.is_end:
                    # wait for next item
                    await data_queue.next_data_future
                    return (
                        await receive()
                    )  # consume again because multiple receives maybe called
            else:
                return data_queue.queue.get(False)  # consume queue

        # no more body, just empty
        return EMPTY_RESPONSE

    async def send(options):
        if bool(aborted[0]):
            return False
        type = options["type"]
        if type == "http.response.start":
            # can also be more native optimized to do it in one GIL call
            # try socketify_res_write_int_status_with_headers and create and socketify_res_cork_write_int_status_with_headers
            status_code = options.get("status", 200)
            headers = options.get("headers", [])
            cork_data = ffi.new_handle((ssl, status_code, headers))
            lib.uws_res_cork(
                ssl, response, uws_asgi_corked_response_start_handler, cork_data
            )
            return True

        if type == "http.response.body":

            # native optimized end/send
            message = options.get("body", b"")

            if options.get("more_body", False):
                if isinstance(message, bytes):
                    lib.socketify_res_cork_write(ssl, response, message, len(message))
                elif isinstance(message, str):
                    data = message.encode("utf-8")
                    lib.socketify_res_cork_write(ssl, response, data, len(data))
            else:
                if isinstance(message, bytes):
                    lib.socketify_res_cork_end(ssl, response, message, len(message), 0)
                elif isinstance(message, str):
                    data = message.encode("utf-8")
                    lib.socketify_res_cork_end(ssl, response, data, len(data), 0)

            return True
        return False

    app._run_task(app.app(scope, receive, send))
    

class _ASGI:
    def __init__(self, app, options=None, websocket=True, websocket_options=None, task_factory_max_items=100_000, lifespan=True):
        self.server = App(options, task_factory_max_items=0)
        self.SERVER_PORT = None
        self.SERVER_HOST = ""
        self.SERVER_SCHEME = "https" if self.server.options else "http"
        self.SERVER_WS_SCHEME = "wss" if self.server.options else "ws"
        self.task_factory_max_items = task_factory_max_items
        self.lifespan = lifespan

        loop = self.server.loop.loop
        # ASGI do not use app.run_async to not add any overhead from socketify.py WebFramework
        # internally will still use custom task factory for pypy because of Loop
        if is_pypy:
            if task_factory_max_items > 0:
                factory = create_task_with_factory(task_factory_max_items)
                
                def run_task(task):
                    factory(loop, task_wrapper(task))
                    loop._run_once()
                self._run_task = run_task
            else:
                def run_task(task):
                    create_task(loop, task_wrapper(task))
                    loop._run_once()
                self._run_task = run_task
            
        else:
            if sys.version_info >= (3, 8): # name fixed to avoid dynamic name
                def run_task(task):
                    future = loop.create_task(task_wrapper(task), name='socketify.py-request-task')
                    future._log_destroy_pending = False
                    loop._run_once()
                self._run_task = run_task
            else:
                def run_task(task):
                    future = loop.create_task(task_wrapper(task))
                    future._log_destroy_pending = False
                    loop._run_once()
                self._run_task = run_task
            

        self.app = app
        self.ws_compression = False
        # optimized in native
        self._ptr = ffi.new_handle(self)
        self.asgi_http_info = lib.socketify_add_asgi_http_handler(
            self.server.SSL, self.server.app, asgi, self._ptr
        )
        self.asgi_ws_info = None
        if isinstance(websocket, dict):  # serve websocket as socketify.py
            if websocket_options:
                websocket.update(websocket_options)

            self.server.ws("/*", websocket)
        elif websocket:  # serve websocket as ASGI

            native_options = ffi.new("uws_socket_behavior_t *")
            native_behavior = native_options[0]

            if not websocket_options:
                websocket_options = {}

            self.ws_compression = bool(websocket_options.get("compression", False))

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
            native_behavior.subscription = ffi.NULL

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
        self.server.listen(port_or_options, handler)
        return self

    def run(self):
        if not self.lifespan:
            print("No lifespan!")
            self.server.run()  
            return self

        scope = {"type": "lifespan", "asgi": {"version": "3.0", "spec_version": "2.3"}}
        
        lifespan_loop = Loop(lambda loop, error, response:  logging.error("Uncaught Exception: %s" % str(error)))
        is_starting = True
        is_stopped = False
        status = 0 # 0 starting, 1 ok, 2 error, 3 stoping, 4 stopped, 5 stopped with error, 6 no lifespan
        status_message = ""
        stop_future = lifespan_loop.create_future()
        async def send(options):
            nonlocal status, status_message, is_stopped
            type = options["type"]
            status_message = options.get("message", "")
            if type == "lifespan.startup.complete":
                status = 1
            elif type == "lifespan.startup.failed":
                is_stopped = True
                status = 2
            elif type == "lifespan.shutdown.complete":
                is_stopped = True
                status = 4
            elif type == "lifespan.shutdown.failed":
                is_stopped = True
                status = 5

        async def receive():
            nonlocal is_starting, is_stopped
            while not is_stopped:
                if is_starting:
                    is_starting = False
                    return {
                        "type": "lifespan.startup",
                        "asgi": {"version": "3.0", "spec_version": "2.3"},
                    }
                return await stop_future

        async def task_wrapper(task):
            nonlocal status
            try:
                return await task
            except Exception as error:
                try:
                    # just log in console the error to call attention
                    logging.error("Uncaught Exception: %s" % str(error))
                    status = 6 # no more lifespan
                finally:
                    return None

        # start lifespan
        lifespan_loop.ensure_future(task_wrapper(self.app(scope, receive, send)))

        # run until start or fail
        while status == 0: 
            lifespan_loop.run_once()

        # failed to start
        if status == 2:
            logging.error("Startup failed: %s" % str(status_message))
            return self

        # run app
        self.server.run()  
        
        # no more lifespan events
        if status == 6:
            return self
        
        # signal stop
        status = 3
        stop_future.set_result({
            "type": "lifespan.shutdown",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
        })

         # run until end or fail
        while status == 3:
            lifespan_loop.run_once()

        # failed to stop
        if status == 5:
            logging.error("Shutdown failed: %s" % str(status_message))
        return self

    def __del__(self):
        if self.asgi_http_info:
            lib.socketify_destroy_asgi_app_info(self.asgi_http_info)
        if self.asgi_ws_info:
            lib.socketify_destroy_asgi_ws_app_info(self.asgi_ws_info)


# "Public" ASGI interface to allow easy forks/workers
class ASGI:
    def __init__(
        self,
        app,
        options=None,
        websocket=True,
        websocket_options=None,
        task_factory_max_items=100_000, #default = 100k = +20mib in memory
        lifespan=True
    ):
        self.app = app
        self.options = options
        self.websocket = websocket
        self.websocket_options = websocket_options
        self.listen_options = None
        self.task_factory_max_items = task_factory_max_items
        self.lifespan = lifespan

    def listen(self, port_or_options, handler=None):
        self.listen_options = (port_or_options, handler)
        return self

    def run(self, workers=1):
        def run_task():
            server = _ASGI(
                self.app,
                self.options,
                self.websocket,
                self.websocket_options,
                self.task_factory_max_items,
            )
            if self.listen_options:
                (port_or_options, handler) = self.listen_options
                server.listen(port_or_options, handler)
            server.run()

        def create_fork():
            n = os.fork()
            # n greater than 0 means parent process
            if not n > 0:
                run_task()

        # fork limiting the cpu count - 1
        for _ in range(1, workers):
            create_fork()

        run_task()  # run app on the main process too :)
        return self
