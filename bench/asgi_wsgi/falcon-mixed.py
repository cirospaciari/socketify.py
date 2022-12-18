import falcon
import falcon.asgi

class Home:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Hello, World!"

class WebSocket:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Connect via ws protocol!"

    async def on_websocket(self, req, ws):
        try:
            await ws.accept()
            while True:
                payload = await ws.receive_text()
                if payload:
                    await ws.send_text(payload)
                    
        except falcon.WebSocketDisconnected:
            print("Disconnected!")



# falcon WSGI APP
app = falcon.App()
home = Home()
app.add_route("/", home)

# ASGI WebSockets Falcon APP
ws = falcon.asgi.App()
ws.add_route("/", WebSocket())