
# CLI Tools

You can use CLI tools to run ASGI, WSGI or socketify.py apps.
```bash
python3 -m socketify --help
```
```bash
Usage: python -m socketify APP [OPTIONS] 
       python3 -m socketify APP [OPTIONS]
       pypy3 -m socketify APP [OPTIONS]

Options:
    --help                                              Show this Help
    --host or -h TEXT                                   Bind socket to this host.  [default:127.0.0.1]
    --port or -p INTEGER                                Bind socket to this port.  [default: 8000]
    --workers or -w INTEGER                             Number of worker processes. Defaults to the WEB_CONCURRENCY 
                                                        environment variable if available, or 1
        
    --uds TEXT                                          Bind to a UNIX domain socket, this options disables --host or -h and --port or -p.
    --ws [auto|none|module:ws]                          If informed module:ws will auto detect to use socketify.py or ASGI websockets
                                                        interface and disabled if informed none [default: auto]
    --ws-max-size INTEGER                               WebSocket max size message in bytes [default: 16777216]
    --ws-auto-ping BOOLEAN                              WebSocket auto ping sending  [default: True]
    --ws-idle-timeout INT                               WebSocket idle timeout  [default: 20]
    --ws-reset-idle-on-send BOOLEAN                     Reset WebSocket idle timeout on send [default: True]
    --ws-per-message-deflate BOOLEAN                    WebSocket per-message-deflate compression [default: False]
    --ws-max-lifetime INT                               Websocket maximum socket lifetime in seconds before forced closure, 0 to disable [default: 0]
    --ws-max-backpressure INT                           WebSocket maximum backpressure in bytes [default: 16777216]
    --ws-close-on-backpressure-limit BOOLEAN            Close connections that hits maximum backpressure [default: False]
    --lifespan [auto|on|off]                            Lifespan implementation.  [default: auto]
    --interface [auto|asgi|asgi3|wsgi|ssgi|socketify]   Select ASGI (same as ASGI3), ASGI3, WSGI or SSGI as the application interface. [default: auto]
    --disable-listen-log BOOLEAN                        Disable log when start listenning [default: False]
    --version or -v                                     Display the socketify.py version and exit.
    --ssl-keyfile TEXT                                  SSL key file
    --ssl-certfile TEXT                                 SSL certificate file
    --ssl-keyfile-password TEXT                         SSL keyfile password
    --ssl-ca-certs TEXT                                 CA certificates file
    --ssl-ciphers TEXT                                  Ciphers to use (see stdlib ssl module's) [default: TLSv1]
    --req-res-factory-maxitems INT                      Pre allocated instances of Response and Request objects for socketify interface [default: 0]
    --ws-factory-maxitems INT                           Pre allocated instances of WebSockets objects for socketify interface [default: 0]
    --task-factory-maxitems INT                         Pre allocated instances of Task objects for socketify, ASGI interface [default: 100000]
Example:
    python3 -m socketify main:app -w 8 -p 8181 

```


Socketify apps requires you to pass an run function, the cli will create the instance for you

```python
from socketify import App
# App will be created by the cli with all things you want configured
def run(app: App): 
    # add your routes here
    app.get("/", lambda res, req: res.end("Hello World!"))
```


 WebSockets can be in the same or another module, you can still use .ws("/*) to serve Websockets
 ```bash
 python3 -m socketify hello_world_cli:run --ws hello_world_cli:ws --port 8080 --workers 2
 ``` 

Socketify.py hello world + websockets:

 ```python
from socketify import App, OpCode
# App will be created by the cli with all things you want configured
def run(app: App): 
    # add your routes here
    app.get("/", lambda res, req: res.end("Hello World!"))

 ws = {
    "open": lambda ws: ws.send("Hello World!", OpCode.TEXT),
    "message": lambda ws, message, opcode: ws.send(message, opcode),
    "close": lambda ws, code, message: print("WebSocket closed"),
}
```

When running ASGI websocket will be served by default, but you can disabled it
 ```bash
 python3 -m socketify falcon_asgi:app --ws none --port 8080 --workers 2
 ``` 
 
When running WSGI or ASGI you can still use socketify.py or ASGI websockets in the same server, mixing all available methods
You can use WSGI to more throughput in HTTP and use ASGI for websockets for example or you can use ASGI/WSGI for HTTP to keep compatibility and just re-write the websockets to use socketify interface with pub/sub and all features
 ```bash
 python3 -m socketify falcon_wsgi:app --ws falcon_wsgi:ws --port 8080 --workers 2
 ``` 

Falcon WSGI + socketify websocket code sample
 ```python
import falcon
from socketify import OpCode

class Home:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Hello, World!"

# falcon APP
app = falcon.App()
home = Home()
app.add_route("/", home)

# socketify websocket app
ws = {
    "open": lambda ws: ws.send("Hello World!", OpCode.TEXT),
    "message": lambda ws, message, opcode: ws.send(message, opcode),
    "close": lambda ws, code, message: print("WebSocket closed"),
}
```

Mixing ASGI websockets + WSGI HTTP

 ```bash
 python3 -m socketify main:app --ws main:ws --port 8080 --workers 2
 ``` 

```python
import falcon
import falcon.asgi

class Home:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Hello, World!"

class WebSocket:
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
```
### Next [API Reference](api.md)