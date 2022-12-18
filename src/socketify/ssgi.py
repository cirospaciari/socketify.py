from socketify import App, CompressOptions, OpCode
from typing import Union, Callable, Awaitable, Optional
import inspect
from queue import SimpleQueue


class SSGIHttpResponse:
    extensions: Optional[dict] = None # extensions for http

    def __init__(self, res, req, extensions = None):
        self.res = res
        self.req = req
        self._need_cork = False
        self._received_queue = None
        self._miss_receive_queue = None
        self.extensions = extensions
    # if payload is None, request ends without body
    # if has_more is True, data is written but connection will not end
    def send(self, payload: Union[str, bytes, bytearray, memoryview, None], has_more: Optional[bool] = False):
        if has_more:
            self.res.write(payload)
        else:
            self.res.end(payload)

    # send chunk of data, can be used to perform with less backpressure than using send
    # total_size is the sum of all lengths in bytes of all chunks to be sended
    # connection will end when total_size is met
    # returns tuple(bool, bool) first bool represents if the chunk is succefully sended, the second if the connection has ended
    def send_chunk(self, chunk: Union[bytes, bytearray, memoryview], total_size: int) -> Awaitable:
        return self.res.send_chunk(chunk, total_size)

    # send status code
    def send_status(self, status_code: Optional[Union[int, str]] = '200 OK'):
        self.res.write_status(status_code)

    # send headers to the http response
    def send_headers(self, headers):
        for name, value in headers:
            self.res.write_header(name, value)

    # ensure async call for the handler, passing any arguments to it
    def run_async(self, handler: Awaitable, *arguments) -> Awaitable:
        self.req.get_headers() # preserve headers
        return self.res.run_async(handler(*arguments))

    # get an all data
    # returns an BytesIO() or None if no payload is available
    def get_data(self) -> Awaitable:
        if self.res.get_header("content-length", False) or self.res.get_header("transfer-encoding", False):
            return self.res.get_data()

        #return empty result
        future = self.res.loop.create_future()
        future.set_result(None)
        return future

    # get an chunk of data (chunk size is decided by the Server implementation)
    # returns the bytes or None if no more chunks are sent
    def get_chunk(self) -> Awaitable:
        if not self._received_queue:
            self._miss_receive_queue = SimpleQueue()
            self._received_queue = SimpleQueue()
            def on_data(res, chunk, is_end):
                if not self._received_queue.empty():
                    future = self._received_queue.get(False)
                    future.set_result(chunk)
                    if not self._received_queue.empty() and is_end and chunk:
                        future = self._received_queue.get(False)
                        future.set_result(None)
                        return
                else:
                    self._miss_receive_queue.put(chunk, False)             
                
                if is_end and chunk:
                    self._miss_receive_queue.put(None, False)

            future = self.res.loop.create_future()
            self._received_queue.put(future, False)
            self.res.on_data(on_data)
            return future
        else:
            future = self.res.loop.create_future()
            if not self._miss_receive_queue.empty():
                future.set_result(self._miss_receive_queue.get(False))
                return future
            self._received_queue.put(future, False)
            return future

    # on aborted event, called when the connection abort
    def on_aborted(self, handler: Union[Awaitable, Callable], *arguments):
        def on_aborted(res):
            res.aborted = True
            if inspect.iscoroutinefunction(handler):
                res.run_async(handler(*arguments))
            else:
                handler(*arguments)

        self.res.on_aborted(on_aborted)
        
class SSGIWebSocket:
    status: int = 0 # 0 pending upgrade, 1 rejected, 2 closed, 3 accepted
    extensions: Optional[dict] = None # extensions for websocket
    def __init__(self, res, req, socket_context, ws, extensions = None):
        self.res = res
        self.req = req
        self.status = 0
        self.extensions = extensions
        self._socket_context = socket_context
        self._key = self.req.get_header("sec-websocket-key")
        self._protocol = self.req.get_header("sec-websocket-protocol")
        self._extensions = self.req.get_header("sec-websocket-extensions")
        self._close_handler = None
        self._receive_handler = None
        self._need_cork = False
        self._accept_future = None

    # accept the connection upgrade
    # can pass the protocol to accept if None is informed will use sec-websocket-protocol header if available
    def accept(self, protocol: str = None) -> Awaitable:
        if self.status == 0:
            self._accept_future = self.res.loop.create_future()
            upgrade_protocol = protocol if protocol else self._protocol

            self.res.upgrade(self._key, upgrade_protocol if upgrade_protocol else "", self._extensions, self._socket_context, self)
            return self._accept_future
        future = self.res.loop.create_future()
        future.set_result(False)
        return future

    # reject the connection upgrade, you can send status_code, payload and headers if you want, all optional
    def reject(self, status_code: Optional[int] = 403, payload = None, headers = None) -> Awaitable:
        
        future = self.res.loop.create_future()
        if self.status < 1: 
            self.status = 1
            if headers:
                for name, value in headers:
                    self.res.write_header(name, value)
            if not payload:
                self.res.write_status(status_code).end_without_body()
            else:
                self.res.write_status(status_code).cork_end(payload)
            future.set_result(True)
        else:
            future.set_result(False)
        return future

    # if returns an future, this can be awaited or not
    def send(self, payload: Union[bytes, bytearray, memoryview]):
        if self.status == 3:
            if self._need_cork:
                self.ws.cork_send(payload)
            else:
                self.ws.send(payload)

    # close connection
    def close(self, code: Optional[int] = 1000):
        if self.status == 3:
            self.ws.close()
            return True
        return False
    # ensure async call for the handler, passing any arguments to it
    def run_async(self, handler: Awaitable, *arguments) -> Awaitable:
        self.req.get_headers()
        self._need_cork = True
        return self.res.run_async(handler(*arguments))

    # on receive event, called when the socket disconnect
    # passes ws: SSGIWebSocket, msg: Union[str, bytes, bytearray, memoryview, None], *arguments
    def on_receive(self, handler: Union[Awaitable, Callable], *arguments):
        def on_receive_handler(ws, message, opcode):
            if inspect.iscoroutinefunction(handler):
                ws.res.run_async(handler(ws, message, *arguments))
            else:
                handler(ws, message, *arguments)
        self._receive_handler = on_receive_handler

    # on close event, called when the socket disconnect
    # passes ws: SSGIWebSocket, code: int and reason: Optional[str] = None, *arguments
    def on_close(self, handler: Union[Awaitable, Callable], *arguments):
        def on_close_handler(ws, code, message):
            if inspect.iscoroutinefunction(handler):
                ws.res.run_async(handler(ws, code, message, *arguments))
            else:
                handler(ws, code, message, *arguments)

        self._close_handler = on_close_handler

class SSGI:
    def __init__(self, app, options=None, request_response_factory_max_items=0, websocket_factory_max_itens=0):
        self.server = App(options, request_response_factory_max_items, websocket_factory_max_itens) 
        self.SERVER_PORT = None
        self.SERVER_HOST = ''
        self.SERVER_SCHEME = 'https' if self.server.options else 'http'
        self.SERVER_WS_SCHEME = 'wss' if self.server.options else 'ws'
        self.SERVER_ADDRESS = ''

        self.app = app
        support = app.get_supported({ "ssgi": "1.0" })
        http, middleware = support.get('http', (None, None))
        websocket, ws_middleware = support.get('websocket', (None, None))

        def ssgi(res, req):

            response = SSGIHttpResponse(res, req)
            PATH_INFO = req.get_url()
            # FULL_PATH_INFO =  req.get_full_url()
            METHOD = req.get_method()
            QUERY_STRING = "" #FULL_PATH_INFO[len(PATH_INFO):]
            
            # REMOTE_ADDRESS = res.get_remote_address()
            def get_header(name = None):
                if name:
                    return req.get_header(name)
                else:
                    return req.get_headers()
            # self.SERVER_SCHEME, self.SERVER_ADDRESS,
            # self.SERVER_SCHEME, self.SERVER_ADDRESS,
            if inspect.iscoroutinefunction(middleware):
                req.get_headers() # preserve
                res.run_async(middleware('http', METHOD, PATH_INFO, QUERY_STRING, get_header, response))
            else:
                middleware('http', METHOD, PATH_INFO, QUERY_STRING, get_header, response)
                # if not response._responded:
                #     res.grab_aborted_handler()
        
        if http == "ssgi" and middleware:
            self.server.any("/*", ssgi) 

        def ws_upgrade(res, req, socket_context):
            response = SSGIWebSocket(res, req, socket_context, None)
            PATH_INFO = req.get_url()
            FULL_PATH_INFO =  req.get_full_url()
            METHOD = req.get_method()
            
            REMOTE_ADDRESS = req.get_remote_address()
            def get_header(name = None):
                if name:
                    return req.get_header(name)
                else:
                    return req.get_headers()
            if inspect.iscoroutinefunction(ws_middleware):
                req.get_headers() # preserve
                res.run_async(ws_middleware('websocket', self.SERVER_SCHEME, self.SERVER_ADDRESS, REMOTE_ADDRESS, METHOD, PATH_INFO, FULL_PATH_INFO[len(PATH_INFO):], get_header, response))
                return
            else:
                ws_middleware('websocket', self.SERVER_WS_SCHEME, self.SERVER_HOST, REMOTE_ADDRESS, METHOD, PATH_INFO, FULL_PATH_INFO[len(PATH_INFO):], get_header, response)            
                # not accepted (async?)
                if response.status == 0 and not response._accept_future:
                    res.grab_aborted_handler()
                
        if websocket == "ssgi" and ws_middleware:
            def ws_open(ws):
                res = ws.get_user_data()
                res.ws = ws
                res.status = 3
                res._accept_future.set_result(True)
            
            def ws_message(ws, message, op):
                res = ws.get_user_data()
                if res._receive_handler:
                    res._receive_handler(res, message, op)
            
            def ws_close(ws, code, message):
                res = ws.get_user_data()
                if res._close_handler:
                    res._close_handler(res, code, message)
                

            self.server.ws("/*", {
                "compression": CompressOptions.DISABLED,
                "max_payload_length": 16 * 1024 * 1024,
                "idle_timeout": 0,
                "upgrade": ws_upgrade,
                "open": ws_open,
                "message": ws_message,
                "close": ws_close
            })

    def listen(self, port_or_options, handler):
        self.SERVER_PORT = port_or_options if isinstance(port_or_options, int) else port_or_options.port
        self.SERVER_HOST = "0.0.0.0" if isinstance(port_or_options, int) else port_or_options.host
        if self.SERVER_PORT:
            self.SERVER_ADDRESS = f"{self.SERVER_HOST}:{self.SERVER_PORT}"
        else:
            self.SERVER_ADDRESS = self.SERVER_HOST

        self.server.listen(port_or_options, handler)
        return self
    def run(self):
        self.server.run()
        return self