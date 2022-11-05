# socketify.py
[![MacOS Build](https://github.com/cirospaciari/socketify.py/actions/workflows/macos.yml/badge.svg)](https://github.com/cirospaciari/socketify.py/actions/workflows/macos.yml)
[![Linux Build](https://github.com/cirospaciari/socketify.py/actions/workflows/linux.yml/badge.svg)](https://github.com/cirospaciari/socketify.py/actions/workflows/linux.yml)
[![Windows Build](https://github.com/cirospaciari/socketify.py/actions/workflows/windows.yml/badge.svg)](https://github.com/cirospaciari/socketify.py/actions/workflows/windows.yml)

Fast WebSocket and Http/Https server using CFFI with C API from [uNetworking/uWebSockets](https://github.com/uNetworking/uWebSockets)

This project aims at High Performance PyPy3 Web Development and WebSockets

> This project will adapt the full C API from uNetworking/uWebSockets, this same C API is used by [Bun](https://bun.sh/)

### Overly simple hello world app [click here](https://github.com/cirospaciari/socketify.py/tree/main/examples) for more examples
```python
from socketify import App

app = App()
app.get("/", lambda res, req: res.end("Hello World socketify from Python!"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()
```


### pip install

```bash
pip install git+https://github.com/cirospaciari/socketify.py.git
#or specify PyPy3
pypy3 -m pip install git+https://github.com/cirospaciari/socketify.py.git
#or in editable mode
pypy3 -m pip install -e git+https://github.com/cirospaciari/socketify.py.git@main#egg=socketify
```

### Install via requirements.txt

requirements.txt file content
```text
git+https://github.com/cirospaciari/socketify.py.git@main#socketify
```

install command
```bash
pip install -r ./requirements.txt 
#or specify PyPy3
pypy3 -m pip install -r ./requirements.txt 
```

### SSL version sample
``` python
from socketify import App, AppOptions

app = App(AppOptions(key_file_name="./misc/key.pem", cert_file_name="./misc/cert.pem", passphrase="1234"))
app.get("/", lambda res, req: res.end("Hello World socketify from Python!"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()
```

### Build local from source
```bash
#clone and update submodules
git clone https://github.com/cirospaciari/socketify.py.git
cd ./socketify.py
git submodule update --init --recursive --remote
#install local pip
pypy3 -m pip install .
#install in editable mode
pypy3 -m pip install -e .
#if you want to remove
pypy3 -m pip uninstall socketify
```
