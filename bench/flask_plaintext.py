import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.CRITICAL) 

from flask import Flask
from waitress import serve

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

serve(app, host='0.0.0.0', port=8000)
