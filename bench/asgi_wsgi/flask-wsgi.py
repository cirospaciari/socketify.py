from flask import Flask, make_response, request
from socketify import WSGI

app = Flask(__name__)

@app.route('/')
def index():
    """Test 6: Plaintext"""
    response = make_response(b"Hello, World!")
    response.content_type = "text/plain"
    return response

@app.route('/post', methods=['POST'])
def post_test():
    """Test 6: Plaintext"""
    user = request.form["name"]
    response = make_response(f"Hello, World {user}!")
    response.content_type = "text/plain"
    return response


if __name__ == "__main__":
    WSGI(app).listen(8000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()

