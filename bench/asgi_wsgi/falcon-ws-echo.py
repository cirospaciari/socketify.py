import falcon.asgi
import falcon.media
from socketify import ASGI


class SomeResource:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Connect via ws protocol!"

    async def on_websocket(self, req, ws):
        try:
            await ws.accept()
            await ws.send_text("hello!")
            while True:
                payload = await ws.receive_text()
                await ws.send_text(payload)

        except falcon.WebSocketDisconnected:
            pass


app = falcon.asgi.App()
app.add_route("/", SomeResource())
# python3 -m gunicorn falcon_server:app -b 127.0.0.1:4001 -w 1 -k uvicorn.workers.UvicornWorker
# pypy3 -m gunicorn falcon_server:app -b 127.0.0.1:4001 -w 1 -k uvicorn.workers.UvicornH11Worker

if __name__ == "__main__":
    ASGI(app).listen(8000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()
