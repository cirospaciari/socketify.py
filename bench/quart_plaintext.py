#!/usr/bin/env python3

from quart import Quart


app = Quart(__name__)

@app.get("/")
async def plaintext():
    return "Hello, World!", {"Content-Type": "text/plain"}

# Quart perform really baddly for sure needs more optimizations, but socketify ASGI + PyPy performs better than uvicorn+httptools+gunicorn