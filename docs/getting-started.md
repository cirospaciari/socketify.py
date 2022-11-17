## Getting Started.

First we need to install following this [Installation Guide](installation.md).

Now that we have everything setup let's take a look in some quick examples.

Hello world app
```python
from socketify import App

app = App()
app.get("/", lambda res, req: res.end("Hello World socketify from Python!"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()
```
> This example just show how intuitive is to start an simple hello world app.

SSL version sample
``` python
from socketify import App, AppOptions

app = App(AppOptions(key_file_name="./misc/key.pem", cert_file_name="./misc/cert.pem", passphrase="1234"))
app.get("/", lambda res, req: res.end("Hello World socketify from Python!"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()
```

> We have a lot of SSL options, but this is the most common you can see all the options in the [API Reference](api.md)

WebSockets
```python
from socketify import App, AppOptions, OpCode, CompressOptions

def ws_open(ws):
    print('A WebSocket got connected!')
    ws.send("Hello World!", OpCode.TEXT)

def ws_message(ws, message, opcode):
    #Ok is false if backpressure was built up, wait for drain
    ok = ws.send(message, opcode)
    
app = App()    
app.ws("/*", {
    'compression': CompressOptions.SHARED_COMPRESSOR,
    'max_payload_length': 16 * 1024 * 1024,
    'idle_timeout': 12,
    'open': ws_open,
    'message': ws_message,
    'drain': lambda ws: print('WebSocket backpressure: %i' % ws.get_buffered_amount()),
    'close': lambda ws, code, message: print('WebSocket closed')
})
app.any("/", lambda res,req: res.end("Nothing to see here!'"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % (config.port)))
app.run()
```

> We can have multiple routes for WebSockets, but in this example we just get one for anything we need, adding an option of compression using SHARED_COMPRESSOR, max_payload_length of 1mb and an idle timeout of 12s just to show some most commonly used features you can see all these options in the [API Reference](api.md)


If you just wanna to see some more examples you can go to our [examples folder](https://github.com/cirospaciari/socketify.py/tree/main/examples) for more than 25 quick examples.
