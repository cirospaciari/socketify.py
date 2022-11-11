# socketify.py


<p align="center">
  <a href="https://github.com/cirospaciari/socketify.py"><img src="https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/logo.png" alt="Logo" height=170></a>
  <br />
  <br />
  <a href="https://github.com/cirospaciari/socketify.py/actions/workflows/macos.yml" target="_blank"><img src="https://github.com/cirospaciari/socketify.py/actions/workflows/macos.yml/badge.svg" /></a>
  <a href="https://github.com/cirospaciari/socketify.py/actions/workflows/linux.yml" target="_blank"><img src="https://github.com/cirospaciari/socketify.py/actions/workflows/linux.yml/badge.svg" /></a>
  <a href="https://github.com/cirospaciari/socketify.py/actions/workflows/windows.yml" target="_blank"><img src="https://github.com/cirospaciari/socketify.py/actions/workflows/windows.yml/badge.svg" /></a>
<a href="https://github.com/sponsors/cirospaciari/" target="_blank"><img src="https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&link=https://github.com/sponsors/cirospaciari"/></a>
</p>



socketify.py brings:

- WebSocket with pub/sub support
- Fast and realiable Http/Https
- Support for Windows, Linux and macOS Silicon & x64
- Support for [`PyPy3`](https://www.pypy.org/) and [`CPython`](https://github.com/python/cpython)
    

This project aims to bring high performance PyPy3 web development and will bring:
- Fetch like API powered by libuv
- Async file IO powered by libuv
- Full asyncio integration with libuv
- Full Http3 support
- [`HPy`](https://hpyproject.org/) integration to better support [`CPython`](https://github.com/python/cpython), [`PyPy`](https://www.pypy.org/) and [`GraalPython`](https://github.com/oracle/graalpython)

We created and adapt the full C API from [uNetworking/uWebSockets](https://github.com/uNetworking/uWebSockets) and will integrate libuv powered fetch and file IO, this same C API is used by [Bun](https://bun.sh/)

**socketify is experimental software at the moment, but quickly heading towards its first release**. Join Github Discussions for help and have a look at things that don’t work yet.

## socketify.py vs japronto

People really want to compare with japronto, but this projects are not really comparable. Socketify is an active project and will be maintained over time with security updates and new features, japronto don't get any github updates since 2020 and don't get any src update since 2018, japronto don't support SSL, WebSockets, [`PyPy3`](https://www.pypy.org/), Windows or macOS Silicon, socketify will support Http3 and a lot more features. 

And yes, we can be faster than japronto when all our features and goals are achieved, and we are probably faster than any current maintained solution out there.

## uvloop
We don't use uvloop, because uvloop don't support Windows and PyPy3 at this moment, this can change in the future, but right now we want to implement our own libuv + asyncio solution, and a lot more.

## CFFI vs Cython vs HPy
Cython performs really well on Python3 but really bad on PyPy3, CFFI are choosen for better support PyPy3 until we got our hands on an stable [`HPy`](https://hpyproject.org/) integration.

## Benchmarks
HTTP requests per second (Linux x64)

![image](https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/bench-bar-graph.svg)

WebSocket messages per second (Linux x64)

![image](https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/ws-bar-graph.svg)


We got almost 900k messages/s with PyPy3 and 860k with Python3 the same performance as [Bun](https://bun.sh) that also uses uWebSockets and Falcon at 35k messages/s and Falcon with PyPy3 improves into 56k messages/s, node.js manages 192k.

Runtime versions: PyPy3 7.3.9, Python 3.10.7, node v16.17.0, bun v0.2.2<br/>
Framework versions: gunicorn 20.1.0 + uvicorn 0.19.0, socketify alpha, gunicorn 20.1.0 + falcon 3.1.0, robyn 0.18.3<br/>
Http tested with oha -c 40 -z 5s http://localhost:8000/ (1 run for warmup and 3 runs average for testing)<br/>
WebSocket tested with [Bun.sh](https://bun.sh) bench chat-client <br/>
Source code in [bench](https://github.com/cirospaciari/socketify.py/tree/main/bench)<br/>

Machine OS: Debian GNU/Linux bookworm/sid x86_64 Kernel: 6.0.0-2-amd64 CPU: Intel i7-7700HQ (8) @ 3.800GHz Memory: 32066MiB 

> Today socketify have about 30% performance hit due to workarounds between asyncio + libuv, so we will got even faster! See more info in [this issue](https://github.com/cirospaciari/socketify.py/issues/18), Python3 and PyPy3 performance will improve when we migrate to [HPy](https://github.com/cirospaciari/socketify.py/issues/16). In TechEmPower benchmarks we are faster than japronto in plaintext (about 1,300k req/s using PyPy3 without workaround and about 770k req/s with the current state vs 582k from japronto you can follow details in [this discussion](https://github.com/cirospaciari/socketify.py/discussions/10)

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

## Commercially supported
I'm a Brazilian consulting & contracting company dealing with anything related with [socketify.py](https://github.com/cirospaciari/socketify.py) and [socketify.rb](https://github.com/cirospaciari/socketify.rb)

Don't hesitate sending a mail if you are in need of advice, support, or having other business inquiries in mind. We'll figure out what's best for both parties.

Special thank's to [uNetworking AB](https://github.com/uNetworking) to develop [uWebSockets](https://github.com/uNetworking/uWebSockets), [uSockets](https://github.com/uNetworking/uSockets) and allow us to bring this features and performance to Python and PyPy

## Sponsors
If you like to see this project thrive, you can sponsor us on GitHub too. We need all the help we can get 

<a href="https://github.com/sponsors/cirospaciari/" target="_blank"><img src="https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&link=https://github.com/sponsors/cirospaciari"/></a>

## Stargazers
[![Stargazers repo roster for @cirospaciari/socketify.py](https://reporoster.com/stars/dark/cirospaciari/socketify.py)](https://github.com/cirospaciari/socketify.py/stargazers)

## Forkers
[![Forkers repo roster for @cirospaciari/socketify.py](https://reporoster.com/forks/dark/cirospaciari/socketify.py)](https://github.com/cirospaciari/socketify.py/network/members)

