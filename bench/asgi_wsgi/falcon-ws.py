import falcon.asgi
import falcon.media
from socketify import ASGI

clients = set([])
remaining_clients = 16


async def broadcast(message):
    # some clients got disconnected if we tried to to all async :/
    # tasks = [ws.send_text(message) for ws in client]
    # return await asyncio.wait(tasks, return_when=ALL_COMPLETED)
    for ws in clients:
        await ws.send_text(message)


class SomeResource:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Connect via ws protocol!"

    async def on_websocket(self, req, ws):
        global remaining_clients
        try:
            await ws.accept()
            clients.add(ws)
            remaining_clients -= 1
            print("remaining_clients", remaining_clients)
            if remaining_clients == 0:
                await broadcast("ready")

            while True:
                payload = await ws.receive_text()
                if payload:
                    await broadcast(payload)

        except falcon.WebSocketDisconnected:
            clients.remove(ws)
            remaining_clients += 1
            print("remaining_clients", remaining_clients)


app = falcon.asgi.App()
app.ws_options.max_receive_queue = 20_000_000# this virtual disables queue but adds overhead
app.ws_options.enable_buffered_receiver = True # this disable queue but for now only available on cirospaciari/falcon
app.add_route("/", SomeResource())
# python3 -m gunicorn falcon_server:app -b 127.0.0.1:4001 -w 1 -k uvicorn.workers.UvicornWorker
# pypy3 -m gunicorn falcon_server:app -b 127.0.0.1:4001 -w 1 -k uvicorn.workers.UvicornH11Worker

if __name__ == "__main__":
    ASGI(app).listen(4001, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()
