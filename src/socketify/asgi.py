from socketify import App, CompressOptions, OpCode
from queue import SimpleQueue
from .native import lib, ffi
import asyncio 

EMPTY_RESPONSE = { 'type': 'http.request', 'body': b'', 'more_body': False }

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

@ffi.callback("void(int, uws_res_t*, socketify_asgi_ws_data, uws_socket_context_t* socket, void*, bool*)")
def ws_upgrade(ssl, response, info, socket_context, user_data, aborted):        
    app = ffi.from_handle(user_data)
    headers = []
    next_header = info.header_list 
    while next_header != ffi.NULL:
        header = next_header[0]
        headers.append((ffi.unpack(header.name, header.name_size),ffi.unpack(header.value, header.value_size)))
        next_header = ffi.cast("socketify_header*", next_header.next)

    url = ffi.unpack(info.url, info.url_size)

    if info.key == ffi.NULL:
        key = None
    else:
        key = ffi.unpack(info.key, info.key_size).decode('utf8')
            
    if info.protocol == ffi.NULL:
        protocol = None
    else:
        protocol = ffi.unpack(info.protocol, info.protocol_size).decode('utf8')
    if info.extensions == ffi.NULL:
        extensions = None
    else:
        extensions = ffi.unpack(info.extensions, info.extensions_size).decode('utf8')
    ws = ASGIWebSocket(app.server.loop)
    scope = {
        'type': 'websocket', 
        'asgi': {
            'version': '3.0', 
            'spec_version': '2.3'
        }, 
        'http_version': '1.1', 
        'server': (app.SERVER_HOST, app.SERVER_PORT), 
        'client': (ffi.unpack(info.remote_address, info.remote_address_size).decode('utf8'), None), 
        'scheme': app.SERVER_WS_SCHEME, 
        'method': ffi.unpack(info.method, info.method_size).decode('utf8'), 
        'root_path': '', 
        'path': url.decode('utf8'), 
        'raw_path': url, 
        'query_string': ffi.unpack(info.query_string, info.query_string_size), 
        'headers': headers,
        'subprotocols': [protocol] if protocol else [],
        'extensions': { 'websocket.publish': True, 'websocket.subscribe': True,  'websocket.unsubscribe': True } 
    }
    async def send(options):
        if bool(aborted[0]): return False
        type = options['type']
        if type == 'websocket.send':
           data = options.get("bytes", None)             
           if ws.ws:
                if data:
                    lib.socketify_ws_cork_send(ssl, ws.ws, data, len(data), int(OpCode.BINARY))
                else:
                    data = options.get('text', '').encode('utf8')
                    lib.socketify_ws_cork_send(ssl, ws.ws, data, len(data), int(OpCode.TEXT))
                return True
           return False
        if type == 'websocket.accept': # upgrade!
            res_headers = options.get('headers', None)
            if res_headers:
                cork_data = ffi.new_handle((ssl, res_headers))
                lib.uws_res_cork(ssl, response, uws_asgi_corked_ws_accept_handler, cork_data)

            future = ws.accept()
            upgrade_protocol = options.get('subprotocol', protocol)

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
        if type == 'websocket.close': # code and reason?
            if ws.ws: 
                lib.uws_ws_close(ssl, ws.ws)
            else: 
                cork_data = ffi.new_handle(ssl)
                lib.uws_res_cork(ssl, response, uws_asgi_corked_403_handler, cork_data)
            return True
        if type == 'websocket.publish': # publish extension
            data = options.get("bytes", None)
            if data: 
                app.server.publish(options.get('topic'), data)
            else:
                app.server.publish(options.get('topic'), options.get('text',  ''), OpCode.TEXT)
            return True
        if type == 'websocket.subscribe': # subscribe extension
            if ws.ws: 
                topic = options.get('topic')
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
        if type == 'websocket.unsubscribe': # unsubscribe extension
            if ws.ws: 
                topic = options.get('topic')
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
    app.server.run_async(app.app(scope, ws.receive, send))

@ffi.callback("void(uws_res_t*, const char*, size_t, bool, void*)")
def asgi_on_data_handler(res, chunk, chunk_length, is_end, user_data):
    data_response = ffi.from_handle(user_data)
    data_response.is_end = bool(is_end)
    more_body = not data_response.is_end
    result = {
        'type': 'http.request',
        'body': b'' if chunk == ffi.NULL else ffi.unpack(chunk, chunk_length), 
        'more_body': more_body
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
        self.miss_receive_queue.put({
                'type': 'websocket.connect'
        }, False)
        self._code = None
        self._message = None
        self._ptr = ffi.new_handle(self)

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
            future.set_result({
                'type': 'websocket.disconnect',
                'code': self._code,
                'message': self._message
            })
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
            future.set_result({
                'type': 'websocket.disconnect',
                'code': code,
                'message': message
            })
        
        

    def message(self, ws, value, opcode):
        self.ws = ws
        if self.receive_queue.empty():
            if opcode == OpCode.TEXT:
                 self.miss_receive_queue.put({
                     'type': 'websocket.receive',
                     'text': value
                 }, False)
            elif opcode == OpCode.BINARY:    
                self.miss_receive_queue.put({
                    'type': 'websocket.receive',
                    'bytes': value
                }, False)
            return True


        future = self.receive_queue.get(False)
        if opcode == OpCode.TEXT:
            future.set_result({
                'type': 'websocket.receive',
                'text': value
            })
        elif opcode == OpCode.BINARY:    
            future.set_result({
                'type': 'websocket.receive',
                'bytes': value
            })
        
        

def write_header(ssl, res, key, value):
    if isinstance(key, str):
        if key == "content-length": return #auto
        key_data = key.encode("utf-8")
    elif isinstance(key, bytes):
        if key == b'content-length': return #auto
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
def uws_asgi_corked_response_start_handler(res, user_data):
    (ssl, status, headers) = ffi.from_handle(user_data)
    lib.socketify_res_write_int_status(ssl, res, int(status))
    for name, value in headers:
        write_header(ssl, res, name, value)
    write_header(ssl, res, b'Server', b'socketify.py')

@ffi.callback("void(uws_res_t*, void*)")
def uws_asgi_corked_accept_handler(res, user_data):
    (ssl, status, headers) = ffi.from_handle(user_data)
    lib.socketify_res_write_int_status(ssl, res, int(status))
    for name, value in headers:
        write_header(ssl, res, name, value)
    write_header(ssl, res, b'Server', b'socketify.py')

@ffi.callback("void(uws_res_t*, void*)")
def uws_asgi_corked_ws_accept_handler(res, user_data):
    (ssl, headers) = ffi.from_handle(user_data)
    for name, value in headers:
        write_header(ssl, res, name, value)
    write_header(ssl, res, b'Server', b'socketify.py')

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
        headers.append((ffi.unpack(header.name, header.name_size),ffi.unpack(header.value, header.value_size)))
        next_header = ffi.cast("socketify_header*", next_header.next)
    url = ffi.unpack(info.url, info.url_size)
    scope = {
        'type': 'http', 
        'asgi': {
            'version': '3.0', 
            'spec_version': '2.3'
        }, 
        'http_version': '1.1', 
        'server': (app.SERVER_HOST, app.SERVER_PORT), 
        'client': (ffi.unpack(info.remote_address, info.remote_address_size).decode('utf8'), None), 
        'scheme': app.SERVER_SCHEME, 
        'method': ffi.unpack(info.method, info.method_size).decode('utf8'), 
        'root_path': '', 
        'path': url.decode('utf8'), 
        'raw_path': url, 
        'query_string': ffi.unpack(info.query_string, info.query_string_size), 
        'headers': headers
    }
    if bool(info.has_content):
         data_queue = ASGIDataQueue(app.server.loop)
         lib.uws_res_on_data(
            ssl, response, asgi_on_data_handler, data_queue._ptr
        )
    else:
        data_queue = None
    async def receive():
        if bool(aborted[0]): 
            return { 'type': 'http.disconnect'}
        if data_queue:
            if data_queue.queue.empty(): 
                if not data_queue.is_end:
                    #wait for next item
                    await data_queue.next_data_future
                    return await receive() #consume again because multiple receives maybe called
            else:
                return data_queue.queue.get(False) #consume queue

        # no more body, just empty
        return EMPTY_RESPONSE
    async def send(options):
        if bool(aborted[0]): 
            return False
        type = options['type']
        if type == 'http.response.start':
            #can also be more native optimized to do it in one GIL call
            #try socketify_res_write_int_status_with_headers and create and socketify_res_cork_write_int_status_with_headers
            status_code = options.get('status', 200)
            headers = options.get('headers', [])
            cork_data = ffi.new_handle((ssl, status_code, headers))
            lib.uws_res_cork(ssl, response, uws_asgi_corked_response_start_handler, cork_data)
            return True

        if type == 'http.response.body':

            #native optimized end/send
            message = options.get('body', b'')
            
            if isinstance(message, str):
                data = message.encode("utf-8")
            elif isinstance(message, bytes):
                data = message
            else:
                data = b''
            if options.get('more_body', False):
                lib.socketify_res_cork_write(ssl, response, data, len(data))
            else:
                lib.socketify_res_cork_end(ssl, response, data, len(data), 0)
            return True
        return False
        
    app.server.loop.run_async(app.app(scope, receive, send))
class ASGI:
    def __init__(self, app, options=None, request_response_factory_max_itens=0, websocket_factory_max_itens=0):
        self.server = App(options, request_response_factory_max_itens, websocket_factory_max_itens) 
        self.SERVER_PORT = None
        self.SERVER_HOST = ''
        self.SERVER_SCHEME = 'https' if self.server.options else 'http'
        self.SERVER_WS_SCHEME = 'wss' if self.server.options else 'ws'

        self.app = app
        # optimized in native
        self._ptr = ffi.new_handle(self)
        self.asgi_http_info = lib.socketify_add_asgi_http_handler(
            self.server.SSL,
            self.server.app,
            asgi,
            self._ptr
        )

        native_options = ffi.new("uws_socket_behavior_t *")
        native_behavior = native_options[0]
        
        native_behavior.maxPayloadLength = ffi.cast(
            "unsigned int",
            16 * 1024 * 1024,
        )
        native_behavior.idleTimeout = ffi.cast(
            "unsigned short",
            0,
        )
        native_behavior.maxBackpressure = ffi.cast(
            "unsigned int",
            1024 * 1024 * 1024,
        )
        native_behavior.compression = ffi.cast(
            "uws_compress_options_t", 0
        )
        native_behavior.maxLifetime = ffi.cast(
            "unsigned short", 0
        )
        native_behavior.closeOnBackpressureLimit = ffi.cast(
            "int", 0
        )
        native_behavior.resetIdleTimeoutOnSend = ffi.cast(
            "int", 0
        )
        native_behavior.sendPingsAutomatically = ffi.cast(
            "int", 0
        )

        native_behavior.upgrade = ffi.NULL # will be set first on C++

        native_behavior.open = ws_open
        native_behavior.message = ws_message
        native_behavior.ping = ffi.NULL
        native_behavior.pong = ffi.NULL
        native_behavior.close = ws_close
        
        self.asgi_ws_info = lib.socketify_add_asgi_ws_handler(
            self.server.SSL,
            self.server.app,
            native_behavior,
            ws_upgrade,
            self._ptr
        )

    def listen(self, port_or_options, handler=None):
        self.SERVER_PORT = port_or_options if isinstance(port_or_options, int) else port_or_options.port
        self.SERVER_HOST = "0.0.0.0" if isinstance(port_or_options, int) else port_or_options.host
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