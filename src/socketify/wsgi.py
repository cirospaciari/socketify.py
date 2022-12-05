

import os
from socketify import App
from io import BytesIO
from .native import lib, ffi

@ffi.callback("void(uws_res_t*, const char*, size_t, bool, void*)")
def wsgi_on_data_handler(res, chunk, chunk_length, is_end, user_data):
    data_response = ffi.from_handle(user_data)
    if chunk != ffi.NULL:
        data_response.buffer.write(ffi.unpack(chunk, chunk_length))
    if bool(is_end):
        lib.uws_res_cork(data_response.app.server.SSL, res, wsgi_corked_response_start_handler, data_response._ptr)
    

class WSGIDataResponse:
    def __init__(self, app, environ, start_response, aborted, buffer, on_data):
        self.buffer = buffer
        self.aborted = aborted
        self._ptr = ffi.new_handle(self)
        self.on_data = on_data
        self.environ = environ
        self.app = app
        self.start_response = start_response

def write(ssl, res, message):
    if isinstance(message, str):
        data = message.encode("utf-8")
    elif isinstance(message, bytes):
        data = message
    else:
        data = b''
    lib.uws_res_write(ssl, res, data, len(data))

def write_status(ssl, res, status_text):
    if isinstance(status_text, str):
        data = status_text.encode("utf-8")
    elif isinstance(status_text, bytes):
        data = status_text
    else:
        return False
    lib.uws_res_write_status(ssl, res, data, len(data))
    return True

def write_header(ssl, res, key, value):
    if isinstance(key, str):
        if key.lower() == "content-length": return #auto
        if key.lower() == "transfer-encoding": return #auto
        key_data = key.encode("utf-8")
    elif isinstance(key, bytes):
        if key.lower() == b'content-length': return #auto
        if key.lower() == b'transfer-encoding': return #auto
        key_data = key

    if isinstance(value, int):
        lib.uws_res_write_header_int(
            ssl,
            res,
            key_data,
            len(key_data),
            ffi.cast("uint64_t", value),
        )
    elif isinstance(value, str):
        value_data = value.encode("utf-8")
    elif isinstance(value, bytes):
        value_data = value
    lib.uws_res_write_header(
        ssl, res, key_data, len(key_data), value_data, len(value_data)
    )

@ffi.callback("void(uws_res_t*, void*)")
def wsgi_corked_response_start_handler(res, user_data):
    data_response = ffi.from_handle(user_data)
    data_response.on_data(data_response, res)

@ffi.callback("void(int, uws_res_t*, socketify_asgi_data request, void*, bool*)")
def wsgi(ssl, response, info, user_data, aborted):    
    app = ffi.from_handle(user_data)

    environ = dict(app.BASIC_ENVIRON)

    environ['REQUEST_METHOD'] = ffi.unpack(info.method, info.method_size).decode('utf8')
    environ['PATH_INFO'] = ffi.unpack(info.url, info.url_size).decode('utf8')
    environ['QUERY_STRING'] = ffi.unpack(info.query_string, info.query_string_size).decode('utf8')
    environ['REMOTE_ADDR'] = ffi.unpack(info.remote_address, info.remote_address_size).decode('utf8')

    next_header = info.header_list 
    while next_header != ffi.NULL:
        header = next_header[0]
        name = ffi.unpack(header.name, header.name_size).decode('utf8')
        value = ffi.unpack(header.value, header.value_size).decode('utf8')
        # this conversion should be optimized in future
        environ[f"HTTP_{name.replace('-', '_').upper()}"]=value
        next_header = ffi.cast("socketify_header*", next_header.next)
    def start_response(status, headers):
        write_status(ssl, response, status)
        for (name, value) in headers:
            write_header(ssl, response, name, value)
        write_header(ssl, response, b'Server', b'socketify.py')
    # check for body
    if bool(info.has_content): 
        WSGI_INPUT = BytesIO()
        environ['wsgi.input'] = WSGI_INPUT
        def on_data(data_response, response):
            if bool(data_response.aborted[0]):
                return

            ssl = data_response.app.server.SSL
            app_iter = data_response.app.app(data_response.environ, data_response.start_response)
            try:
                for data in app_iter:
                    write(ssl, response, data)
            finally:
                if hasattr(app_iter, 'close'):
                    app_iter.close()
            lib.uws_res_end_without_body(ssl, response, 0)
            
        data_response = WSGIDataResponse(app, environ, start_response, aborted, WSGI_INPUT, on_data)

        lib.uws_res_on_data(
            ssl, response, wsgi_on_data_handler, data_response._ptr
        )
    else:
        environ['wsgi.input'] = None
        app_iter = app.app(environ, start_response)
        try:
            for data in app_iter:
                write(ssl, response, data)
        finally:
            if hasattr(app_iter, 'close'):
                app_iter.close()
        lib.uws_res_end_without_body(ssl, response, 0)

class WSGI:
    def __init__(self, app, options=None, request_response_factory_max_itens=0, websocket_factory_max_itens=0):
        self.server = App(options, request_response_factory_max_itens, websocket_factory_max_itens) 
        self.SERVER_PORT = None
        self.app = app
        self.BASIC_ENVIRON = dict(os.environ)

        self._ptr = ffi.new_handle(self)
        self.asgi_http_info = lib.socketify_add_asgi_http_handler(
            self.server.SSL,
            self.server.app,
            wsgi,
            self._ptr
        )

    def listen(self, port_or_options, handler=None):
        self.SERVER_PORT = port_or_options if isinstance(port_or_options, int) else port_or_options.port
        self.BASIC_ENVIRON.update({
            'GATEWAY_INTERFACE': 'CGI/1.1', 
            'SERVER_PORT': str(self.SERVER_PORT), 
            'SERVER_SOFTWARE': 'WSGIServer/0.2', 
            'wsgi.input': None,
            'wsgi.errors': None, 
            'wsgi.version': (1, 0),
            'wsgi.run_once': False, 
            'wsgi.url_scheme':  'https' if self.server.options else 'http', 
            'wsgi.multithread': False, 
            'wsgi.multiprocess': False, 
            'wsgi.file_wrapper': None, # No file wrapper support for now
            'SCRIPT_NAME': '',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'REMOTE_HOST': '',
        })
        self.server.listen(port_or_options, handler)
        return self
    def run(self):
        self.server.run()
        return self
