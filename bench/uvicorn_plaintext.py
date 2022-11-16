async def app(scope, receive, send):
    assert scope["type"] == "http"

    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                [b"content-type", b"text/plain"],
            ],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": b"Hello, world!",
        }
    )


# python3 -m gunicorn uvicorn_guvicorn_plaintext:app -w 1 -k uvicorn.workers.UvicornWorker
# pypy3 -m gunicorn uvicorn_guvicorn_plaintext:app -w 1 -k uvicorn.workers.UvicornWorker
