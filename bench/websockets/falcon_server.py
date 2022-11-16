import falcon.asgi
import falcon.media
import asyncio

clients = set([])
remaining_clients = 16


async def broadcast(message):
    # some clients got disconnected if we tried to to all async :/
    # tasks = [ws.send_text(message) for ws in client]
    # return await asyncio.wait(tasks, return_when=ALL_COMPLETED)
    for ws in clients:
        await ws.send_text(message)


class SomeResource:
    async def on_get(self, req):
        pass

    async def on_websocket(self, req, ws):
        global remaining_clients
        try:
            await ws.accept()
            clients.add(ws)
            remaining_clients = remaining_clients - 1
            if remaining_clients == 0:
                await broadcast("ready")

            while True:
                payload = await ws.receive_text()
                await broadcast(payload)

        except falcon.WebSocketDisconnected:
            clients.remove(ws)
            remaining_clients = remaining_clients + 1


app = falcon.asgi.App()
app.add_route("/", SomeResource())
# python3 -m gunicorn falcon_server:app -b 127.0.0.1:4001 -w 1 -k uvicorn.workers.UvicornWorker
# pypy3 -m gunicorn falcon_server:app -b 127.0.0.1:4001 -w 1 -k uvicorn.workers.UvicornH11Worker
