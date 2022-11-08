# socketify.py


<p align="center">
  <a href="https://github.com/cirospaciari/socketify.py"><img src="https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/logo.png" alt="Logo" height=170></a>
  <br />
  <br />
  <a href="https://github.com/cirospaciari/socketify.py/actions/workflows/macos.yml" target="_blank"><img src="https://github.com/cirospaciari/socketify.py/actions/workflows/macos.yml/badge.svg" /></a>
  <a href="https://github.com/cirospaciari/socketify.py/actions/workflows/linux.yml" target="_blank"><img src="https://github.com/cirospaciari/socketify.py/actions/workflows/linux.yml/badge.svg" /></a>
  <a href="https://github.com/cirospaciari/socketify.py/actions/workflows/windows.yml" target="_blank"><img src="https://github.com/cirospaciari/socketify.py/actions/workflows/windows.yml/badge.svg" /></a>
</p>



socketify.py brings:

- WebSocket with pub/sub support
- Fast and realiable Http/Https
- Support for Windows, Linux and macOS Silicon & x64
- Support for [`PyPy3`](https://www.pypy.org/) and [`CPython`](https://github.com/python/cpython)
    

This project aims to bring high performance PyPy3 web development and will bring:
- fetch like API powered by libuv
- async file IO powered by libuv
- full asyncio integration with libuv

We created and adapt the full C API from [uNetworking/uWebSockets](https://github.com/uNetworking/uWebSockets) and integrate libuv powered fetch and file IO, this same C API is used by [Bun](https://bun.sh/)

## Benchmark
HTTP requests per second (Linux x64)

| framework | req/s | runtime |
| ------------- | -------------: | :-------------: |
| socketify.py  | 124,943  | PyPy3  |
| socketify.py  | 70,877  | Python3  |
| uvicorn  | 30,173  | Python3  |
| uvicorn  | 17,580  | PyPy3  |

Runtime versions: PyPy3 7.3.9 and Python 3.10.7<br/>
Framework versions: gunicorn 20.1.0 + uvicorn 0.19.0, socketify alpha<br/>
Tested with ./http_load_test 40 127.0.0.1 8000 from [uSockets](https://github.com/uNetworking/uSockets)
Source code in [bench](https://github.com/cirospaciari/socketify.py/tree/main/bench)
> Today socketify have about 30% performance hit due to workarounds between asyncio + libuv, so we will got even faster! See more info in [this issue](https://github.com/cirospaciari/socketify.py/issues/18), in PyPy3 we can get about 186,760 req/s and 77,774 req/s in Python3 without these workarounds and almost double of the scores with PyPy3 in TechEmPower plaintext, Python3 and PyPy3 performance will improve when we migrate to [HPy](https://github.com/cirospaciari/socketify.py/issues/16). In TechEmPower benchmarks we are faster than japronto in plaintext (about 1,300k req/s using PyPy3 without workaround and about 770k req/s with the current state vs 582k from japronto you can follow details in [this discussion](https://github.com/cirospaciari/socketify.py/discussions/10)

## Install
For macOS x64 & Silicon, Linux x64, Windows

```bash
pip install git+https://github.com/cirospaciari/socketify.py.git
#or specify PyPy3
pypy3 -m pip install git+https://github.com/cirospaciari/socketify.py.git
#or in editable mode
pypy3 -m pip install -e git+https://github.com/cirospaciari/socketify.py.git@main#egg=socketify
```

Using install via requirements.txt
```text
git+https://github.com/cirospaciari/socketify.py.git@main#socketify
```
```bash
pip install -r ./requirements.txt 
#or specify PyPy3
pypy3 -m pip install -r ./requirements.txt 
```

## Examples

Hello world app
```python
from socketify import App

app = App()
app.get("/", lambda res, req: res.end("Hello World socketify from Python!"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()
```

SSL version sample
``` python
from socketify import App, AppOptions

app = App(AppOptions(key_file_name="./misc/key.pem", cert_file_name="./misc/cert.pem", passphrase="1234"))
app.get("/", lambda res, req: res.end("Hello World socketify from Python!"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()
```

We have more than 20 examples [click here](https://github.com/cirospaciari/socketify.py/tree/main/examples) for more

## Build local from source
```bash
#clone and update submodules
git clone https://github.com/cirospaciari/socketify.py.git
cd ./socketify.py
git submodule update --init --recursive --remote
#you can use make linux, make macos or call Make.bat from Visual Studio Development Prompt to build
cd ./src/socketify/native/ && make linux && cd ../../../
#install local pip
pypy3 -m pip install .
#install in editable mode
pypy3 -m pip install -e .
#if you want to remove
pypy3 -m pip uninstall socketify
```
