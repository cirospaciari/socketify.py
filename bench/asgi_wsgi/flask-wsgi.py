from flask import Flask, make_response
from socketify import WSGI

app = Flask(__name__)

@app.route('/')
def index():
    """Test 6: Plaintext"""
    response = make_response(b"Hello, World!")
    response.content_type = "text/plain"
    return response


WSGI(app).listen(8000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()

