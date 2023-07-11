# socketify.py


<p align="center">
  <a href="https://github.com/cirospaciari/socketify.py"><img src="https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/logo.png" alt="Logo" height=170></a>
  <br />
  <br />
  <a href="https://github.com/cirospaciari/socketify.py/actions/workflows/linux.yml" target="_blank"><img src="https://github.com/cirospaciari/socketify.py/actions/workflows/linux.yml/badge.svg" /></a>
  <a href="https://github.com/cirospaciari/socketify.py/actions/workflows/windows.yml" target="_blank"><img src="https://github.com/cirospaciari/socketify.py/actions/workflows/windows.yml/badge.svg" /></a>
<a href="https://github.com/cirospaciari/socketify.py/actions/workflows/macos.yml" target="_blank"><img src="https://github.com/cirospaciari/socketify.py/actions/workflows/macos.yml/badge.svg" /></a>
  <a href="https://github.com/cirospaciari/socketify.py/actions/workflows/macos_arm64.yml" target="_blank"><img src="https://github.com/cirospaciari/socketify.py/actions/workflows/macos_arm64.yml/badge.svg" /></a>
  <br/>
<a href='https://github.com/cirospaciari/socketify.py'><img alt='GitHub Clones' src='https://img.shields.io/badge/dynamic/json?color=success&label=Clones&query=count&url=https://gist.githubusercontent.com/cirospaciari/2243d59951f4abe4fd2000f1e20bc561/raw/clone.json&logo=github'></a>
<a href='https://pypi.org/project/socketify/' target="_blank"><img alt='PyPI Downloads' src='https://static.pepy.tech/personalized-badge/socketify?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads'></a>
<a href="https://github.com/sponsors/cirospaciari/" target="_blank"><img src="https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&link=https://github.com/sponsors/cirospaciari"/></a>
<a href='https://discord.socketify.dev/' target="_blank"><img alt='Discord' src='https://img.shields.io/discord/1042529276219641906?label=Discord'></a>
</p>

<div align="center">
  <a href="https://docs.socketify.dev">Documentation</a>
  <span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
  <a href="https://discord.socketify.dev/">Discord</a>
  <span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
  <a href="https://github.com/cirospaciari/socketify.py/issues">Issues</a>
  <span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
  <a href="https://github.com/cirospaciari/socketify.py/tree/main/examples">Examples</a>
  <br />
</div>

## 💡 Features

- WebSocket with pub/sub support
- Fast and reliable Http/Https
- Support for Windows, Linux and macOS Silicon & x64
- Support for [`PyPy3`](https://www.pypy.org/) and [`CPython`](https://github.com/python/cpython)
- Dynamic URL Routing with Wildcard & Parameter support
- Sync and Async Function Support
- Really Simple API
- Fast and Encrypted TLS 1.3 quicker than most alternative servers can do even unencrypted, cleartext messaging
- Per-SNI HttpRouter Support
- Proxy Protocol v2
- Shared or Dedicated Compression Support
- Max Backpressure, Max Timeout, Max Payload and Idle Timeout Support
- Automatic Ping / Pong Support
- Per Socket Data
- [`Middlewares`](https://docs.socketify.dev/middlewares.html)
- [`Templates`](https://docs.socketify.dev/templates.html) Support (examples with [`Mako`](https://github.com/cirospaciari/socketify.py/tree/main/examples/template_mako.py) and [`Jinja2`](https://github.com/cirospaciari/socketify.py/tree/main/examples/template_jinja2.py))
- [`ASGI Server`](https://docs.socketify.dev/cli.html)
- [`WSGI Server`](https://docs.socketify.dev/cli.html)
- [`Plugins/Extensions`](https://docs.socketify.dev/extensions.html)

## :mag_right: Upcoming Features
- In-Memory Cache Tools
- Fetch like API powered by libuv
- Async file IO powered by libuv
- Full asyncio integration with libuv
- SSGI Server spec and support
- RSGI Server support
- Full Http3 support
- [`HPy`](https://hpyproject.org/) integration to better support [`CPython`](https://github.com/python/cpython), [`PyPy`](https://www.pypy.org/) and [`GraalPython`](https://github.com/oracle/graalpython)
- Hot Reloading

We created and adapted the full C API from [uNetworking/uWebSockets](https://github.com/uNetworking/uWebSockets) and will integrate libuv powered fetch and file IO, this same C API is used by [Bun](https://bun.sh/)

Join Github [`Discussions`](https://github.com/cirospaciari/socketify.py/discussions) or [`Discord`](https://discord.socketify.dev/) for help and have a look at the development progress.

## :zap: Benchmarks
Socketify WebFramework HTTP requests per second (Linux x64)

![image](https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/bench-bar-graph-general.png)

WSGI Server requests per second (Linux x64)

![image](https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/bench-bar-graph-wsgi.png)

ASGI Server requests per second (Linux x64)

![image](https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/bench-bar-graph-asgi.png)

WebSocket messages per second (Linux x64)

![image](https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/bench-bar-graph-websockets.png)


Http tested with TFB tool plaintext benchmark<br/>
WebSocket tested with [Bun.sh](https://bun.sh) bench chat-client <br/>
Source code in [TechEmPower](https://github.com/TechEmpower/FrameworkBenchmarks) and for websockets in [bench](https://github.com/cirospaciari/socketify.py/tree/main/bench)<br/>

Machine OS: Debian GNU/Linux bookworm/sid x86_64 Kernel: 6.0.0-2-amd64 CPU: Intel i7-7700HQ (8) @ 3.800GHz Memory: 32066MiB 

## 📦 Installation
For macOS x64 & Silicon, Linux x64, Windows

```bash
pip install socketify
#or specify PyPy3
pypy3 -m pip install socketify
#or in editable mode
pypy3 -m pip install -e socketify
```

Using install via requirements.txt
```text
socketify
```
```bash
pip install -r ./requirements.txt 
#or specify PyPy3
pypy3 -m pip install -r ./requirements.txt 
```

If you are using linux or macOS, you may need to install libuv and zlib in your system

macOS
```bash
brew install libuv
brew install zlib
```

Linux
```bash
apt install libuv1 zlib1g
```

## 🤔 Usage

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
    'drain': lambda ws: print(f'WebSocket backpressure: {ws.get_buffered_amount()}'),
    'close': lambda ws, code, message: print('WebSocket closed'),
    'subscription': lambda ws, topic, subscriptions, subscriptions_before: print(f'subscription/unsubscription on topic {topic} {subscriptions} {subscriptions_before}'),
})
app.any("/", lambda res,req: res.end("Nothing to see here!'"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % (config.port)))
app.run()
```

We have more than 20 examples [click here](https://github.com/cirospaciari/socketify.py/tree/main/examples) for more

## :hammer: Building from source
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

## :briefcase: Commercially supported
I'm a Brazilian consulting & contracting company dealing with anything related with [socketify.py](https://github.com/cirospaciari/socketify.py) and [socketify.rb](https://github.com/cirospaciari/socketify.rb)

Don't hesitate sending a mail if you are in need of advice, support, or having other business inquiries in mind. We'll figure out what's best for both parties.

Special thank's to [uNetworking AB](https://github.com/uNetworking) to develop [uWebSockets](https://github.com/uNetworking/uWebSockets), [uSockets](https://github.com/uNetworking/uSockets) and allow us to bring this features and performance to Python and PyPy

## :heart: Sponsors
If you like to see this project thrive, you can sponsor us on GitHub too. We need all the help we can get.

Thank you [`Otavio Augusto`](https://github.com/middlebaws) to be the first sponsor of this project!

<a href="https://github.com/sponsors/cirospaciari/" target="_blank"><img src="https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&link=https://github.com/sponsors/cirospaciari"/></a>

## :star: Stargazers
[![Stargazers repo roster for @cirospaciari/socketify.py](https://reporoster.com/stars/dark/cirospaciari/socketify.py)](https://github.com/cirospaciari/socketify.py/stargazers)

## :wrench: Forkers
[![Forkers repo roster for @cirospaciari/socketify.py](https://reporoster.com/forks/dark/cirospaciari/socketify.py)](https://github.com/cirospaciari/socketify.py/network/members)

## :grey_question: uvloop
We don't use uvloop, because uvloop don't support Windows and PyPy3 at this moment, this can change in the future, but right now we want to implement our own libuv + asyncio solution, and a lot more.

## :dizzy: CFFI vs Cython vs HPy
Cython performs really well on Python3 but really bad on PyPy3, CFFI are chosen for better support PyPy3 until we got our hands on a stable [`HPy`](https://hpyproject.org/) integration.

