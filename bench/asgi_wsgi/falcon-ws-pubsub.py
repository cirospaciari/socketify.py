import falcon.asgi
import falcon.media
from socketify import ASGI

remaining_clients = 16

class SomeResource:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Connect via ws protocol!"

    async def on_websocket(self, req, ws):
        global remaining_clients
        try:
            await ws.accept()
            await ws.subscribe('all')
            
            remaining_clients = remaining_clients - 1
            if remaining_clients == 0:
                
                await ws.publish_text('all', 'ready')
            else:
                print("remaining_clients", remaining_clients)

            while True:
                payload = await ws.receive_text()
                await ws.publish_text('all', payload)

        except falcon.WebSocketDisconnected:
            remaining_clients = remaining_clients + 1
            print("remaining_clients", remaining_clients)

app = falcon.asgi.App()
app.ws_options.max_receive_queue = 20_000_000 # this virtual disables queue but adds overhead
app.ws_options.enable_buffered_receiver = False # this disable queue but for now only available on cirospaciari/falcon
app.add_route("/", SomeResource())

if __name__ == "__main__":
    ASGI(app).listen(4001, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()
