from socketify import App, AppOptions, OpCode, CompressOptions

remaining_clients = 16

def ws_open(ws):
    ws.subscribe("room")
    global remaining_clients
    remaining_clients = remaining_clients - 1
    if remaining_clients == 0:
       print("All clients connected")
       print('Starting benchmark by sending "ready" message')
       
       ws.publish("room", "ready", OpCode.TEXT)
       #publish will send to everyone except it self so send to it self too
       ws.send("ready", OpCode.TEXT)
       

def ws_message(ws, message, opcode):
    #publish will send to everyone except it self so send to it self too
    ws.publish("room", message, opcode)
    ws.send(message, opcode)
    
def ws_close(ws, close, message):
    global remaining_clients
    remaining_clients = remaining_clients + 1

app = App()    
app.ws("/*", {
    'compression': CompressOptions.DISABLED,
    'max_payload_length': 16 * 1024 * 1024,
    'idle_timeout': 60,
    'open': ws_open,
    'message': ws_message,
    'close': ws_close
})
app.any("/", lambda res,req: res.end("Nothing to see here!'"))
app.listen(4001, lambda config: print("Listening on port http://localhost:%d now\n" % (config.port)))
app.run()