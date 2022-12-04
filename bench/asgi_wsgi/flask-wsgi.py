from flask import Flask
from socketify import WSGI

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, World!'

def run_app():
    WSGI(app, request_response_factory_max_itens=200_000).listen(8000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()

