from socketify import App, OpCode

def run(app: App): 
    # add your routes here
    app.get("/", lambda res, req: res.end("Hello World!"))
    

# cli will use this configuration for serving in "/*" route, you can still use .ws("/*", config) if you want but --ws* options will not have effect
websocket = {
    "open": lambda ws: ws.send("Hello World!", OpCode.TEXT),
    "message": lambda ws, message, opcode: ws.send(message, opcode),
    "close": lambda ws, code, message: print("WebSocket closed"),
}
# python -m socketify hello_world_cli_ws:run --ws hello_world_cli_ws:websocket --port 8080 --workers 2
# python3 -m socketify hello_world_cli_ws:run --ws hello_world_cli_ws:websocket--port 8080 --workers 2
# pypy3 -m socketify hello_world_cli_ws:run --ws hello_world_cli_ws:websocket--port 8080 --workers 2

# see options in with: python3 -m socketify --help