import os
import inspect
from socketify import App
from .asgi import ws_close, ws_upgrade, ws_open, ws_message
from io import BytesIO, BufferedReader
from .native import lib, ffi
import platform

is_pypy = platform.python_implementation() == "PyPy"
from .tasks import create_task, TaskFactory
import sys
import logging
import uuid

@ffi.callback("void(uws_res_t*, const char*, size_t, bool, void*)")
def wsgi_on_data_handler(res, chunk, chunk_length, is_end, user_data):
    data_response = ffi.from_handle(user_data)
    data_response.app.server.loop.is_idle = False

    if chunk != ffi.NULL:
        data_response.buffer.write(ffi.unpack(chunk, chunk_length))
    if bool(is_end):
        lib.uws_res_cork(
            data_response.app.server.SSL,
            res,
            wsgi_corked_response_start_handler,
            data_response._ptr,
        )

@ffi.callback("void(uws_res_t*, void*)")
def wsgi_on_data_ref_abort_handler(res, user_data):
    data_retry = ffi.from_handle(user_data)
    data_retry.aborted = True
    data_retry.server.loop.is_idle = False
    if data_retry.id is not None:
        data_retry.app._data_refs.pop(data_retry.id, None)    
    

@ffi.callback("bool(uws_res_t*, uintmax_t, void*)")
def wsgi_on_writable_handler(res, offset, user_data):
    data_retry = ffi.from_handle(user_data)
    if data_retry.aborted:
        return False
    
    chunks = data_retry.chunks
    last_sended_offset = data_retry.last_offset
    server = data_retry.app.server
    ssl = server.SSL
    server.loop.is_idle = False
    content_length = data_retry.content_length
    
    data = chunks[0]
    data_size = len(data)
    last_offset = int(lib.uws_res_get_write_offset(ssl, res))
    if last_sended_offset != last_offset:
        offset = last_offset - last_sended_offset
        data = data[offset:data_size]
        data_size = len(data)
        if data_size == 0:
            chunks.pop(0)
        
        if len(chunks) == 0:
            logging.error(AssertionError("Content-Length do not match sended content"))
            lib.uws_res_close(
                ssl,
                res
            )
            if data_retry.id is not None:
                data_retry.app._data_refs.pop(data_retry.id, None)
    
            return True
        data = chunks[0]

    result = lib.uws_res_try_end(
        ssl,
        res,
        data,
        data_size,
        content_length,
        0,
    )
    has_responded = bool(result.has_responded)
    ok = bool(result.ok)
    data_retry.last_offset = int(lib.uws_res_get_write_offset(ssl, res))

    if ok:
        chunks.pop(0)
        if not has_responded and len(chunks) == 0:
            logging.error(AssertionError("Content-Length do not match sended content"))
            lib.uws_res_close(
                ssl,
                res
            )
            if data_retry.id is not None:
                data_retry.app._data_refs.pop(data_retry.id, None)
        elif has_responded and data_retry.id is not None:
            data_retry.app._data_refs.pop(data_retry.id, None)
    elif not has_responded and len(chunks) == 0:
        logging.error(AssertionError("Content-Length do not match sended content"))
        lib.uws_res_close(
            ssl,
            res
        )
        if data_retry.id is not None:
            data_retry.app._data_refs.pop(data_retry.id, None)
    elif has_responded and data_retry.id is not None:
        data_retry.app._data_refs.pop(data_retry.id, None)
    

    return ok

class WSGIBody:
    def __init__(self, buffer):
        self.buf = buffer
        self.reader = BufferedReader(buffer)

    def __iter__(self):
        return self

    def __next__(self):
        ret = self.readline()
        if not ret:
            raise StopIteration()
        return ret

    next = __next__

    def getsize(self, size):
        if size is None:
            return sys.maxsize
        elif not isinstance(size, int):
            raise TypeError("size must be an integral type")
        elif size < 0:
            return sys.maxsize
        return size

    def read(self, size=None):
        size = self.getsize(size)
        if size == 0:
            return b""

        if size < self.buf.tell():
            data = self.buf.getvalue()
            ret, rest = data[:size], data[size:]
            self.buf = BytesIO()
            self.buf.write(rest)
            return ret

        while size > self.buf.tell():
            data = self.reader.read(1024)
            if not data:
                break
            self.buf.write(data)

        data = self.buf.getvalue()
        ret, rest = data[:size], data[size:]
        self.buf = BytesIO()
        self.buf.write(rest)
        return ret

    def readline(self, size=None):
        size = self.getsize(size)
        if size == 0:
            return b""

        data = self.buf.getvalue()
        self.buf = BytesIO()

        ret = []
        while 1:
            idx = data.find(b"\n", 0, size)
            idx = idx + 1 if idx >= 0 else size if len(data) >= size else 0
            if idx:
                ret.append(data[:idx])
                self.buf.write(data[idx:])
                break

            ret.append(data)
            size -= len(data)
            data = self.reader.read(min(1024, size))
            if not data:
                break

        return b"".join(ret)

    def readlines(self, size=None):
        ret = []
        data = self.read()
        while data:
            pos = data.find(b"\n")
            if pos < 0:
                ret.append(data)
                data = b""
            else:
                line, data = data[: pos + 1], data[pos + 1 :]
                ret.append(line)
        return ret


class WSGIDataResponse:
    def __init__(self, app, environ, start_response, buffer, on_data):
        self.buffer = buffer
        self._ptr = ffi.new_handle(self)
        self.on_data = on_data
        self.environ = environ
        self.app = app
        self.start_response = start_response
        self.id = None
        self.aborted = False

class WSGIRetryDataSend:
    def __init__(self, app, chunks, content_length, last_offset):
        self.chunks = chunks
        self._ptr = ffi.new_handle(self)
        self.app = app
        self.content_length = content_length
        self.last_offset = last_offset
        self.id = None
        self.aborted = False


@ffi.callback("void(uws_res_t*, void*)")
def wsgi_corked_response_start_handler(res, user_data):
    data_response = ffi.from_handle(user_data)
    data_response.on_data(data_response, res)



@ffi.callback("void(int, uws_res_t*, socketify_asgi_data request, void*)")
def wsgi(ssl, response, info, user_data):
    app = ffi.from_handle(user_data)
    app.server.loop.is_idle = False

    # reusing the dict is slower than cloning because we need to clear HTTP headers
    environ = dict(app.BASIC_ENVIRON)

    environ["REQUEST_METHOD"] = ffi.unpack(info.method, info.method_size).decode("utf8")
    environ["PATH_INFO"] = ffi.unpack(info.url, info.url_size).decode("utf8")
    environ["QUERY_STRING"] = ffi.unpack(
        info.query_string, info.query_string_size
    ).decode("utf8")[1:]
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

    environ["CONTENT_TYPE"] = environ.get("HTTP_CONTENT_TYPE", "")

    headers_set = None
    headers_written = False
    status_text = None
    is_chunked = False
    content_length = -1
    def write_headers(headers):
        nonlocal headers_written, headers_set, status_text, content_length, is_chunked, app
        if headers_written or not headers_set:
            return
        app.server.loop.is_idle = False

        headers_written = True

        if isinstance(status_text, str):
            data = status_text.encode("utf-8")
            lib.uws_res_write_status(ssl, response, data, len(data))
        elif isinstance(status_text, bytes):
            lib.uws_res_write_status(ssl, response, status_text, len(status_text))

        for (key, value) in headers:
            if isinstance(key, str):
                # this is faster than using .lower()
                if (
                    key == "content-length"
                    or key == "Content-Length"
                ):
                    content_length = int(value)
                    continue  # auto generated by try_end
                if (
                    key == "Transfer-Encoding"
                    or key == "transfer-encoding"
                ):
                    is_chunked = str(value) == "chunked"
                    if is_chunked:
                        continue
                
                key_data = key.encode("utf-8")
            elif isinstance(key, bytes):
                # this is faster than using .lower()
                if (
                    key == b"content-length"
                    or key == b"Content-Length"
                ):
                    content_length = int(value)
                    continue  # auto
                if (
                    key == b"Transfer-Encoding"
                    or key == b"transfer-encoding"
                ):
                    is_chunked = str(value) == "chunked"
                    if is_chunked:
                        continue
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
        # no content-length
        if content_length < 0:
            is_chunked = True
        content_length = ffi.cast("uintmax_t", content_length)

    def start_response(status, headers, exc_info=None):
        nonlocal headers_set, status_text, app
        app.server.loop.is_idle = False
        if exc_info:
            try:
                if headers_written:
                    # Re-raise original exception if headers sent
                    raise exc_info[1].with_traceback(exc_info[2])
            finally:
                exc_info = None  # avoid dangling circular ref
        elif headers_set:
            raise AssertionError("Headers already set!")

        headers_set = headers
        status_text = status

        def write(data):
            nonlocal is_chunked, app
            app.server.loop.is_idle = False
            if not headers_written:
                write_headers(headers_set)
            # will allow older frameworks only with is_chunked
            is_chunked = True 
                
            if isinstance(data, bytes):
                lib.uws_res_write(ssl, response, data, len(data))
            elif isinstance(data, str):
                data = data.encode("utf-8")
                lib.uws_res_write(ssl, response, data, len(data))

        return write

    
    
    
    # check for body
    if bool(info.has_content):
        WSGI_INPUT = BytesIO()
        environ["wsgi.input"] = WSGIBody(WSGI_INPUT)
        def on_data(data_response, response):
            last_offset = -1
            data_retry = None
            failed_chunks = None


            if data_response.aborted:
                return
            data_response.app.server.loop.is_idle = False
            ssl = data_response.app.server.SSL
            data_response.environ["CONTENT_LENGTH"] = str(
                data_response.buffer.getbuffer().nbytes
            )
            if data_response.id is not None:
                data_response.app._data_refs.pop(data_response.id, None)
                
            app_iter = data_response.app.wsgi(
                data_response.environ, data_response.start_response
            )
            
            try:
                for data in app_iter:
                    if data:
                        if not headers_written:
                            write_headers(headers_set)
                            
                        if is_chunked:
                            if isinstance(data, bytes):
                                lib.uws_res_write(ssl, response, data, len(data))
                            elif isinstance(data, str):
                                data = data.encode("utf-8")
                                lib.uws_res_write(ssl, response, data, len(data))
                        else:
                            if isinstance(data, str):
                                data = data.encode("utf-8")
                            if failed_chunks:
                                failed_chunks.append(data)
                            else:
                                last_offset = int(lib.uws_res_get_write_offset(ssl, response))
                                result = lib.uws_res_try_end(
                                    ssl,
                                    response,
                                    data,
                                    len(data),
                                    content_length,
                                    0,
                                )
                                # this should be very very rare for HTTP
                                if not bool(result.ok):
                                    failed_chunks = []
                                    # just mark the chunks
                                    failed_chunks.append(data)
                                    # add on writable handler
                                    data_retry = WSGIRetryDataSend(
                                        app, failed_chunks, content_length, last_offset
                                    )

            except Exception as error:
                logging.exception(error)
            finally:
                if hasattr(app_iter, "close"):
                    app_iter.close()

            if not headers_written:
                write_headers(headers_set)         
            if is_chunked:
                lib.uws_res_end_without_body(ssl, response, 0)
            elif data_retry is not None:
                _id = uuid.uuid4()
                app._data_refs[_id] = data_retry
                lib.uws_res_on_aborted(ssl, response, wsgi_on_data_ref_abort_handler, data_retry._ptr)
                lib.uws_res_on_writable(ssl, response, wsgi_on_writable_handler, data_retry._ptr)
            elif result is None or (not bool(result.has_responded) and bool(result.ok)): # not reaches Content-Length
                logging.error(AssertionError("Content-Length do not match sended content"))
                lib.uws_res_close(
                    ssl,
                    response
                )
        data_response = WSGIDataResponse(
            app, environ, start_response, WSGI_INPUT, on_data
        )
        _id = uuid.uuid4()
        data_response.id = _id
        app._data_refs[_id] = data_response
        lib.uws_res_on_aborted(ssl, response, wsgi_on_data_ref_abort_handler, data_response._ptr)
        lib.uws_res_on_data(ssl, response, wsgi_on_data_handler, data_response._ptr)
    else:
        failed_chunks = None
        last_offset = -1
        data_retry = None
        # Django do not check for None with is lame
        # we use the same empty for everyone to avoid extra allocations
        environ["wsgi.input"] = app.EMPTY_WSGI_BODY
        # we also set CONTENT_LENGTH to 0 so if Django is lame again its covered
        environ["CONTENT_LENGTH"] = "0"
        app_iter = app.wsgi(environ, start_response)
        result = None
        try:
            for data in app_iter:
                if data:
                    if not headers_written:
                        write_headers(headers_set)
                    if is_chunked:
                        if isinstance(data, bytes):
                            lib.uws_res_write(ssl, response, data, len(data))
                        elif isinstance(data, str):
                            data = data.encode("utf-8")
                            lib.uws_res_write(ssl, response, data, len(data))
                    else:
                        if isinstance(data, str):
                            data = data.encode("utf-8")
                        if failed_chunks: # if failed once, will fail again later
                            failed_chunks.append(data)
                        else:
                            last_offset = int(lib.uws_res_get_write_offset(ssl, response))
                            result = lib.uws_res_try_end(
                                ssl,
                                response,
                                data,
                                len(data),
                                content_length,
                                0,
                            )
                            # this should be very very rare for HTTP
                            if not bool(result.ok):
                                failed_chunks = []
                                # just mark the chunks
                                failed_chunks.append(data)
                                # add on writable handler
                                data_retry = WSGIRetryDataSend(
                                    app, failed_chunks, content_length, last_offset
                                )
                        

        except Exception as error:
            logging.exception(error)
        finally:
            if hasattr(app_iter, "close"):
                app_iter.close()

        if not headers_written:
            write_headers(headers_set)         
        if is_chunked:
            lib.uws_res_end_without_body(ssl, response, 0)
        elif data_retry is not None:
            _id = uuid.uuid4()
            data_retry.id = _id
            app._data_refs[_id] = data_retry
            lib.uws_res_on_aborted(ssl, response, wsgi_on_data_ref_abort_handler, data_retry._ptr)
            lib.uws_res_on_writable(ssl, response, wsgi_on_writable_handler, data_retry._ptr)
        elif result is None or (not bool(result.has_responded) and bool(result.ok)): # not reaches Content-Length
            logging.error(AssertionError("Content-Length do not match sended content"))
            lib.uws_res_close(
                ssl,
                response
            )


def is_asgi(module):
    return (
        hasattr(module, "__call__") and len(inspect.signature(module).parameters) == 3
    )


class _WSGI:
    def __init__(
        self,
        app,
        options=None,
        websocket=None,
        websocket_options=None,
        task_factory_max_items=100_000,
    ):
        self.server = App(options, task_factory_max_items=0)
        self.SERVER_HOST = None
        self.SERVER_PORT = None
        self.SERVER_WS_SCHEME = "wss" if self.server._options else "ws"
        self.wsgi = app
        self.EMPTY_WSGI_BODY = WSGIBody(BytesIO())
        self.BASIC_ENVIRON = dict(os.environ)
        self.ws_compression = False
        self._data_refs = {}
        self._ptr = ffi.new_handle(self)
        self.asgi_http_info = lib.socketify_add_asgi_http_handler(
            self.server.SSL, self.server.app, wsgi, self._ptr
        )
        self.asgi_ws_info = None

        if isinstance(websocket, dict):  # serve websocket as socketify.py
            if websocket_options:
                websocket.update(websocket_options)

            self.server.ws("/*", websocket)
        elif is_asgi(websocket):
            self.app = websocket  # set ASGI app
            loop = self.server.loop.loop
            # ASGI do not use app.run_async to not add any overhead from socketify.py WebFramework
            # internally will still use custom task factory for pypy because of Loop
            if is_pypy:
                if task_factory_max_items > 0:
                    factory = TaskFactory(task_factory_max_items)

                    def run_task(task):
                        factory(loop, task)

                    self._run_task = run_task
                else:

                    def run_task(task):
                        future = create_task(loop, task)
                        future._log_destroy_pending = False

                    self._run_task = run_task

            else:
                if sys.version_info >= (3, 8):  # name fixed to avoid dynamic name

                    def run_task(task):
                        future = create_task(loop, task)
                        future._log_destroy_pending = False

                    self._run_task = run_task
                else:

                    def run_task(task):
                        future = create_task(loop, task)
                        future._log_destroy_pending = False

                    self._run_task = run_task

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
        self.BASIC_ENVIRON.update(
            {
                "GATEWAY_INTERFACE": "CGI/1.1",
                "SERVER_PORT": str(self.SERVER_PORT),
                "SERVER_SOFTWARE": "WSGIServer/0.2",
                "wsgi.input": None,
                "wsgi.errors": sys.stderr,
                "wsgi.version": (1, 0),
                "wsgi.run_once": False,
                "wsgi.url_scheme": "https" if self.server._options and self.server._options.cert_file_name is not None else "http",
                "wsgi.multithread": False,
                "wsgi.multiprocess": False,
                "wsgi.file_wrapper": None,  # No file wrapper support for now
                "SCRIPT_NAME": "",
                "SERVER_PROTOCOL": "HTTP/1.1",
                "REMOTE_HOST": "",
                "CONTENT_LENGTH": "0",
                "CONTENT_TYPE": "",
                "wsgi.input_terminated": True,
            }
        )
        self.server.listen(port_or_options, handler)
        return self

    def run(self):
        self.server.run()
        return self

    def __del__(self):
        try:
            if self.asgi_http_info:
                lib.socketify_destroy_asgi_app_info(self.asgi_http_info)
            if self.asgi_ws_info:
                lib.socketify_destroy_asgi_ws_app_info(self.asgi_ws_info)
        except:
            pass


# "Public" WSGI interface to allow easy forks/workers
class WSGI:
    def __init__(
        self,
        app,
        options=None,
        websocket=None,
        websocket_options=None,
        task_factory_max_items=100_000,
        lifespan=False,
    ):
        self.app = app
        self.options = options
        self.websocket = websocket
        self.websocket_options = websocket_options
        self.listen_options = None
        self.task_factory_max_items = task_factory_max_items
        self.server = None
        self.pid_list = None
        # lifespan is not supported in WSGI

    def listen(self, port_or_options, handler=None):
        self.listen_options = (port_or_options, handler)
        return self

    def close(self):
        # always wait a sec so forks can start properly if close is called too fast
        import time
        time.sleep(1)
        
        if self.server is not None:
            self.server.close()
        if self.pid_list is not None:
            import signal
            for pid in self.pid_list:
                os.kill(pid, signal.SIGINT)

    def run(self, workers=1, block=True):
        def run_task():
            server = _WSGI(
                self.app,
                self.options,
                self.websocket,
                self.websocket_options,
                self.task_factory_max_items,
            )
            if self.listen_options:
                (port_or_options, handler) = self.listen_options
                server.listen(port_or_options, handler)
            self.server = server
            server.run()

        pid_list = []
        
        start = 1 if block else 0
        # fork limiting the cpu count - 1
        for _ in range(start, workers):
            pid = os.fork()
            # n greater than 0 means parent process
            if not pid > 0:
                run_task()
                break
            pid_list.append(pid)

        self.pid_list = pid_list

        if block:
            run_task()  # run app on the main process too :)
            # sigint everything to graceful shutdown
            import signal
            for pid in pid_list:
                os.kill(pid, signal.SIGINT)

        return self
