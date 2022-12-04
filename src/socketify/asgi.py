from socketify import App, CompressOptions, OpCode
from queue import SimpleQueue
from .native import lib, ffi

# Just an IDEA, must be implemented in native code (Cython or HPy), is really slow use this way
# re encoding data and headers is really dummy (can be consumed directly by ffi), dict ops are really slow
EMPTY_RESPONSE = { 'type': 'http.request', 'body': b'', 'more_body': False }

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
        key_data = key.encode("utf-8")
    elif isinstance(key, bytes):
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
    lib.socketify_res_write_int_status(ssl, res, status)
    for name, value in headers:
        write_header(ssl, res, name, value)
    write_header(ssl, res, b'Server', b'socketify.py')


@ffi.callback("void(int, uws_res_t*, socketify_asgi_data request, void*, bool*)")
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
    async def receive():
        if bool(aborted[0]): 
            return { 'type': 'http.disconnect'}
        # if scope.get("content-length", False) or scope.get("transfer-encoding", False): 
        #     data = await res.get_data()
        #     if data:
        #         # all at once but could get in chunks
        #         return {
        #             'type': 'http.request',
        #             'body': data.getvalue(), 
        #             'more_body': False
        #         }
        # no body, just empty
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

        def ws_upgrade(res, req, socket_context):
            info = lib.socketify_asgi_ws_request(res.SSL, req.req, res.res)
            
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

            ws = ASGIWebSocket(self.server.loop)

            scope = {
                'type': 'websocket', 
                'asgi': {
                    'version': '3.0', 
                    'spec_version': '2.3'
                }, 
                'http_version': '1.1', 
                'server': (self.SERVER_HOST, self.SERVER_PORT), 
                'client': (ffi.unpack(info.remote_address, info.remote_address_size).decode('utf8'), None), 
                'scheme': self.SERVER_WS_SCHEME, 
                'method': ffi.unpack(info.method, info.method_size).decode('utf8'), 
                'root_path': '', 
                'path': url.decode('utf8'), 
                'raw_path': url, 
                'query_string': ffi.unpack(info.query_string, info.query_string_size), 
                'headers': headers,
                'subprotocols': [protocol] if protocol else [],
                'extensions': { 'websocket.publish': True, 'websocket.subscribe': True,  'websocket.unsubscribe': True } 
            }
            lib.socketify_destroy_headers(info.header_list)
            async def send(options):
                if res.aborted: return False
                type = options['type']
                if type == 'websocket.send':
                   bytes = options.get("bytes", None)
                   
                   if ws.ws:
                        if bytes:
                            ws.ws.cork_send(bytes, OpCode.BINARY)
                        else:
                            ws.ws.cork_send(options.get('text', ''), OpCode.TEXT)
                        return True
                   return False

                if type == 'websocket.accept': # upgrade!
                    res_headers = options.get('headers', None)
                    def corked(res):
                        for header in res_headers:
                            res.write_header(header[0], header[1])
                    if res_headers:
                        res.cork(corked)

                    future = ws.accept()
                    upgrade_protocol = options.get('subprotocol', protocol)
                    res.upgrade(key, upgrade_protocol if upgrade_protocol else "", extensions, socket_context, ws)
                    return await future
                
                if type == 'websocket.close': # code and reason?
                    if ws.ws: ws.ws.close()
                    else: res.cork(lambda res: res.write_status(403).end_without_body())
                    return True
                if type == 'websocket.publish': # publish extension
                    bytes = options.get("bytes", None)
                    if bytes: 
                        self.server.publish(options.get('topic'), bytes)
                    else:
                        self.server.publish(options.get('topic'), options.get('text',  ''), OpCode.TEXT)
                    return True
                if type == 'websocket.subscribe': # subscribe extension
                    if ws.ws: ws.ws.subscribe(options.get('topic'))
                    else: res.cork(lambda res: res.write_status(403).end_without_body())
                    return True
                if type == 'websocket.unsubscribe': # unsubscribe extension
                    if ws.ws: ws.ws.unsubscribe(options.get('topic'))
                    else: res.cork(lambda res: res.write_status(403).end_without_body())
                    return True
                return False
                
            res.run_async(app(scope, ws.receive, send))
            

        self.server.ws("/*", {
            "compression": CompressOptions.DISABLED,
            "max_payload_length": 16 * 1024 * 1024,
            "idle_timeout": 0,
            "upgrade": ws_upgrade,
            "open": lambda ws: ws.get_user_data().open(ws),
            "message": lambda ws, msg, opcode: ws.get_user_data().message(ws, msg, opcode),
            "close": lambda ws, code, message: ws.get_user_data().disconnect(code, message)
        })

    def listen(self, port_or_options, handler):
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