# uWebSockets.py
Fast WebSocket and Http/Https server using CFFI with C API from [uNetworking/uWebSockets](https://github.com/uNetworking/uWebSockets)

> This project will adapt the full capi from uNetworking/uWebSockets but for now it's just this.

### Overly simple hello world app
```python
from "uws" import App

app = App()
app.get("/", lambda res, req: res.end("Hello World uWS from Python!"))
app.listen(3000, lambda socket, config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()
```

### pip (working progress)

```bash
pip install git+https://github.com/cirospaciari/uWebSockets.py.git
```

### Run
```bash
pypy3 ./hello_world.py
```

### SSL version sample
``` python
from "uws" import App, AppOptions

app = App(AppOptions(key_file_name="./misc/key.pem", cert_file_name="./misc/cert.pem", passphrase="1234"))
app.get("/", plaintext)
app.listen(3000, lambda socket, config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()
```