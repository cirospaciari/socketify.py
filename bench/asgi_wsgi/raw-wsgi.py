from io import BytesIO

payload = None
with open("xml.zip", "rb") as file:
    payload = file.read()


stream = BytesIO()
stream.write(payload)

chunk_size = 64 * 1024
content_length = len(payload)

def app_chunked(environ, start_response):
    start_response('200 OK', [('Content-Type', 'application/zip'), ('Transfer-Encoding', 'chunked')])
    
    sended = 0
    while content_length > sended:
        end = sended + chunk_size
        yield payload[sended:end]
        sended = end
        
    
def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'application/zip'), ('Content-Length', str(content_length))])
    
    sended = 0
    while content_length > sended:
        end = sended + chunk_size
        yield payload[sended:end]
        sended = end

def app_hello(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain'), ('Content-Length', '13')])
    
    yield b'Hello, World!'

if __name__ == "__main__":
    from socketify import WSGI
    WSGI(app_hello).listen(8000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run(1)
    # import fastwsgi
    # fastwsgi.run(wsgi_app=app_hello, host='127.0.0.1', port=8000)
