from socketify import WSGI

def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield b'Hello, World!\n'

if __name__ == "__main__":
    WSGI(app).listen(8000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()

