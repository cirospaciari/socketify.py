

import os
from socketify import App
from io import BytesIO
# Just an IDEA, must be implemented in native code (Cython or HPy), is really slow use this way
# re formatting headers is really slow and dummy, dict ops are really slow

class WSGI:
    def __init__(self, app, options=None, request_response_factory_max_itens=0, websocket_factory_max_itens=0):
        self.server = App(options, request_response_factory_max_itens, websocket_factory_max_itens) 
        self.SERVER_PORT = None
        self.app = app
        self.BASIC_ENVIRON = dict(os.environ)
        def wsgi(res, req):
            # create environ
            PATH_INFO = req.get_url()
            FULL_PATH_INFO =  req.get_full_url()
            environ = dict(self.BASIC_ENVIRON)
            environ['REQUEST_METHOD'] = req.get_method()
            environ['PATH_INFO'] = PATH_INFO
            environ['QUERY_STRING'] = FULL_PATH_INFO[len(PATH_INFO):]
            environ['REMOTE_ADDR'] = res.get_remote_address()
            
            
            def start_response(status, headers):
                res.write_status(status)
                for (name, value) in headers:
                        res.write_header(name, value)


            def set_http(name, value):
                environ[f"HTTP_{name.replace('-', '_').upper()}"]=value
            req.for_each_header(set_http)
 
            #check for body
            if environ.get("HTTP_CONTENT_LENGTH", False) or environ.get("HTTP_TRANSFER_ENCODING", False): 
                WSGI_INPUT = BytesIO()
                environ['wsgi.input'] = WSGI_INPUT
                def on_data(res, chunk, is_end):  
                    if chunk:
                        WSGI_INPUT.write(chunk)
                    if is_end:
                        app_iter = self.app(environ, start_response)
                        try:
                            for data in app_iter:
                                res.write(data)
                        finally:
                            if hasattr(app_iter, 'close'):
                                app_iter.close()
                        res.end_without_body()
                res.on_data(on_data)
            else:
                environ['wsgi.input'] = None
                app_iter = self.app(environ, start_response)
                try:
                    for data in app_iter:
                        res.write(data)
                finally:
                    if hasattr(app_iter, 'close'):
                        app_iter.close()
                res.end_without_body()

        self.server.any("/*", wsgi)


    def listen(self, port_or_options, handler):
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
