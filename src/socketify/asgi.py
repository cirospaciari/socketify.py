from socketify import App, CompressOptions, OpCode
import asyncio
from queue import SimpleQueue
# Just an IDEA, must be implemented in native code (Cython or HPy), is really slow use this way
# re encoding data and headers is really dummy (can be consumed directly by ffi), dict ops are really slow
EMPTY_RESPONSE = { 'type': 'http.request', 'body': b'', 'more_body': False }

class ASGIWebSocket:
    def __init__(self, loop):
        self.loop = loop
        self.accept_future = None
        self.ws = None
        self.receive_queue = SimpleQueue()
        self.miss_receive_queue = SimpleQueue()
        self.miss_receive_queue.put({
                'type': 'websocket.connect'
        }, False)

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
        
        self.receive_queue.put(future, False)
        return future


    def disconnect(self, code, message):
        self.ws = None
        if not self.receive_queue.empty():
            future = self.receive_queue.get(False)
            future.set_result({
                'type': 'websocket.disconnect',
                'code': code,
                'message': message
            })
        else:
            self.miss_receive_queue.put({
                'type': 'websocket.disconnect',
                'code': code,
                'message': message
            }, False)
        
        

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
        
        
class ASGI:
    def __init__(self, app, options=None, request_response_factory_max_itens=0, websocket_factory_max_itens=0):
        self.server = App(options, request_response_factory_max_itens, websocket_factory_max_itens) 
        self.SERVER_PORT = None
        self.SERVER_HOST = ''
        self.SERVER_SCHEME = 'https' if self.server.options else 'http'
        self.SERVER_WS_SCHEME = 'wss' if self.server.options else 'ws'

        self.app = app

        def asgi(res, req):
            PATH_INFO = req.get_url()
            FULL_PATH_INFO =  req.get_full_url()
            headers = []
            req.for_each_header(lambda name, value: headers.append((name.encode('utf8'), value.encode('utf8'))))

            scope = {
                'type': 'http', 
                'asgi': {
                    'version': '3.0', 
                    'spec_version': '2.0'
                }, 
                'http_version': '1.1', 
                'server': (self.SERVER_HOST, self.SERVER_PORT), 
                'client': (res.get_remote_address(), None), 
                'scheme': self.SERVER_SCHEME, 
                'method': req.get_method(), 
                'root_path': '', 
                'path': PATH_INFO, 
                'raw_path': PATH_INFO.encode('utf8'), 
                'query_string': FULL_PATH_INFO[len(PATH_INFO):].encode('utf8'), 
                'headers': headers
            }
            
            async def receive():
                if res.aborted:
                    return { 'type': 'http.disconnect'}

                if scope.get("content-length", False) or scope.get("transfer-encoding", False): 
                    data = await res.get_data()
                    if data:
                        # all at once but could get in chunks
                        return {
                            'type': 'http.request',
                            'body': data.getvalue(), 
                            'more_body': False
                        }
                # no body, just empty
                return EMPTY_RESPONSE
            
            async def send(options):
                if res.aborted: return False
                type = options['type']
                if type == 'http.response.start':
                    res.write_status(options.get('status', 200))
                    for header in options.get('headers', []):
                        res.write_header(header[0], header[1])
                    return True
                
                if type == 'http.response.body':
                    if options.get('more_body', False):
                        res.write(options.get('body', ""))
                    else:
                        res.cork_end(options.get('body', ""))
                    return True
                return False
            #grab handler
            res.grab_aborted_handler()
            asyncio.ensure_future(app(scope, receive, send))
        self.server.any("/*", asgi)    

        def ws_upgrade(res, req, socket_context):
            PATH_INFO = req.get_url()
            FULL_PATH_INFO =  req.get_full_url()
            headers = []
            def filtered_headers(name, value):
                if name != "sec-websocket-protocol":
                    headers.append((name.encode('utf8'), value.encode('utf8')))

            req.for_each_header(filtered_headers)
            key = req.get_header("sec-websocket-key")
            protocol = req.get_header("sec-websocket-protocol")
            extensions = req.get_header("sec-websocket-extensions")

            ws = ASGIWebSocket(self.server.loop)

            scope = {
                'type': 'websocket', 
                'asgi': {
                    'version': '3.0', 
                    'spec_version': '2.0'
                }, 
                'http_version': '1.1', 
                'server': (self.SERVER_HOST, self.SERVER_PORT), 
                'client': (res.get_remote_address(), None), 
                'scheme': self.SERVER_WS_SCHEME, 
                'method': req.get_method(), 
                'root_path': '', 
                'path': PATH_INFO, 
                'raw_path': PATH_INFO.encode('utf8'), 
                'query_string': FULL_PATH_INFO[len(PATH_INFO):].encode('utf8'), 
                'headers': headers,
                'subprotocols': [protocol] if protocol else [],
                'extensions': { 'websocket.publish': True, 'websocket.subscribe': True,  'websocket.unsubscribe': True } 
            }
            server = self.server
            async def send(options):
                nonlocal ws, res, server

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
                    for header in options.get('headers', []):
                        res.write_header(header[0], header[1])
                    future = ws.accept()
                    upgrade_protocol = options.get('subprotocol', protocol)
                    res.upgrade(key, upgrade_protocol if upgrade_protocol else "", extensions, socket_context, ws)
                    return await future
                
                if type == 'websocket.close': # code and reason?
                    if ws.ws: ws.ws.close()
                    else: res.write_status(403).end_without_body()
                    return True
                if type == 'websocket.publish': # publish extension
                    bytes = options.get("bytes", None)
                    if bytes: 
                        server.publish(options.get('topic'), bytes)
                    else:
                        server.publish(options.get('topic'), options.get('text'), OpCode.TEXT)
                    return True
                if type == 'websocket.subscribe': # subscribe extension
                    if ws.ws: ws.ws.subscribe(options.get('topic'))
                    else: res.write_status(403).end_without_body()
                    return True
                if type == 'websocket.unsubscribe': # unsubscribe extension
                    if ws.ws: ws.ws.unsubscribe(options.get('topic'))
                    else: res.write_status(403).end_without_body()
                    return True
                return False
                

            #grab handler
            res.grab_aborted_handler()
            asyncio.ensure_future(app(scope, ws.receive, send))
            

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