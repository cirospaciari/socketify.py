# First Ideas for SSGI

```python
from typing import Union, Callable, Awaitable, Optional

class SSGIHttpResponse:
    aborted: bool = False, # detect if the connection was aborted
    extensions: Optional[dict] = None # extensions for http

    # if payload is None, request ends without body
    # if has_more is True, data is written but connection will not end
    def send(self, payload: Union[str, bytes, bytearray, memoryview, None], has_more: Optional[bool] = False):
        pass

    # send chunk of data, can be used to perform with less backpressure than using send
    # total_size is the sum of all lengths in bytes of all chunks to be sended
    # connection will end when total_size is met
    # returns tuple(bool, bool) first bool represents if the chunk is succefully sended, the second if the connection has ended
    def send_chunk(self, chunk: Union[str, bytes, bytearray, memoryview], total_size: int = False) -> Awaitable:
        pass

    # send status code
    def send_status(self, status_code: Optional[int] = 200):
        pass

    # send headers to the http response
    def send_headers(self, headers: iter(tuple(str, str))):
        pass

    # ensure async call for the handler, passing any arguments to it
    def run_async(self, handler: Awaitable, *arguments) -> Awaitable:
        pass

    # get an all data
    # returns an BytesIO() or None if no payload is available
    def get_data(self) -> Awaitable:
        pass

    # get an chunk of data (chunk size is decided by the Server implementation)
    # returns the BytesIO or None if no more chunks are sent
    def get_chunk(self) -> Awaitable:
        pass

    # on aborted event, called when the connection abort
    def on_aborted(self, handler: Union[Awaitable, Callable], *arguments):
        pass

class SSGIWebSocket:
    status: int = 0 # 0 pending upgrade, 1 rejected, 2 closed, 3 accepted
    extensions: Optional[dict] = None # extensions for websocket

    # accept the connection upgrade
    # can pass the protocol to accept if None is informed will use sec-websocket-protocol header if available
    def accept(self, protocol: str = None) -> Awaitable:
        pass

    # reject the connection upgrade, you can send status_code, payload and headers if you want, all optional
    def reject(self, status_code: Optional[int] = 403, payload: Union[bytes, bytearray, memoryview, None] = None, headers: Optional[iter(tuple(str, str))] = None) -> Awaitable:
        pass

    # if returns an future, this can be awaited or not
    def send(self, payload: Union[bytes, bytearray, memoryview]):
        pass

    # close connection
    def close(self, code: Optional[int] = 1000):
        pass

    # ensure async call for the handler, passing any arguments to it
    def run_async(self, handler: Awaitable, *arguments) -> Awaitable:
        pass

    # on receive event, called when the socket disconnect
    # passes ws: SSGIWebSocket, msg: Union[str, bytes, bytearray, memoryview], *arguments
    def on_receive(self, handler: Union[Awaitable, Callable], *arguments):
        pass

    # on close event, called when the socket disconnect
    # passes ws: SSGIWebSocket, code: int and reason: Optional[str] = None, *arguments
    def on_close(self, handler: Union[Awaitable, Callable], *arguments):
        pass



# only accepts sync
def wsgi(environ, start_response):
    pass
# only accepts async
async def asgi(scope, receive, send):
    pass
# async with less overhead
async def rsgi(scope, proto):
    pass
# async and sync can be used
def ssgi(type: str, server_address: str, remote_address: str, method: str, path: str, query_string: str, get_header: Callable[[Optional[str]=None], [Union[str, iter(tuple(str, str))]], res: Union[SSGIHttpResponse, SSGIWebSocket]):
    # this is called once every HTTP request, or when an websocket connection wants to upgrade
    # type can be http or websocket
    
    # server_address contains {ipv4|ipv6}:{port} being :{port} optional
    # remote_address contains {ipv4|ipv6}:{port} being :{port} optional

    # here routers can work without call any header, this can improve performance because headers are not allocated in
    # if passed get_header() without arguments or None, must return all headers in an dict
    # all headers must be lowercase
    # headers will only be preserved until the end of this call or if res.run_async is called
    # headers are not preserved after websocket accept or reject
    # if this function is an coroutine, data will be preserved, run_async is automatic
    pass

# SSGI do not require that SSGI it self to be implemented, allowing other interfaces to be supported by the Server and Framework as will
class SSGIFramework:
    def get_supported(self, supported_interfaces: dict) -> dict:
        # supported_interfaces { "asgi": "2.3", "wsgi": "2.0", "ssgi": "1.0", "rsgi": "1.0" }
        # you can use this to check what interface is available

        # returns http and websocket interface supported by the Web Framework
        # you can use multiple interfaces one for http and other for websockets with SSGI if the Web Framework and Server supports it
        # if None is passed, Server will not serve the protocol
        # tuple(interface_name, interface_handler)
        return {
            "http": ( "ssgi", ssgi), #or "asgi", "rsgi", "wsgi",
            "websockets": ("ssgi", ssgi)  #or "asgi", "rsgi"
        }

```