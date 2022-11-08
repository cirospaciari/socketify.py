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

<style>
.graph-label{
    --black: #0b0a08;
    --blue: #00a6e1;
    --orange: #f89b4b;
    --orange-light: #d4d3d2;
    --monospace-font: "Fira Code", "Hack", "Source Code Pro", "SF Mono",
          "Inconsolata", monospace;
    --dark-border: rgba(200, 200, 25, 0.2);
    --max-width: 1152px;
    --system-font: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
          Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue",
          sans-serif;
    --horizontal-padding: 3rem;
    --vertical-padding: 4rem;
    --line-height: 1.4;
    list-style-type: none;
    --count: 3;
    --primary: 70px;
    --opposite: 100%;
    box-sizing: border-box;
    --level: calc(var(--amount) / var(--max));
    --inverse: calc(1 / var(--level));
    color: #fff;
    font-variant-numeric: tabular-nums;
    font-family: var(--monospace-font);
    width: 100%;
    text-align: center;
    position: relative;
    display: flex;
    justify-content: center;
    top: -22px;
}
.label-bottom{
    top: unset;
    color: gray;
    bottom: calc(calc(200px * var(--level) * -1) + 20px);
}
.graph-bar{
    --black: #0b0a08;
    --blue: #00a6e1;
    --orange: #f89b4b;
    --orange-light: #d4d3d2;
    --monospace-font: "Fira Code", "Hack", "Source Code Pro", "SF Mono",
          "Inconsolata", monospace;
    --dark-border: rgba(200, 200, 25, 0.2);
    --max-width: 1152px;
    --system-font: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
          Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue",
          sans-serif;
    --horizontal-padding: 3rem;
    --vertical-padding: 4rem;
    --line-height: 1.4;
    color: #fbf0df;
    list-style-type: none;
    font-variant-numeric: tabular-nums;
    font-family: var(--monospace-font);
    --count: 3;
    --level: calc(var(--amount) / var(--max));
    --inverse: calc(1 / var(--level));
    box-sizing: border-box;
    --primary: 70px;
    --opposite: 100%;
    margin: 0 auto;
    width: var(--primary);
    position: relative;
    height: calc(200px * var(--level));
    background-color: #5d5986;
}
.socketify{
    background-color: gray;
    box-shadow: inset 1px 1px 3px #ccc6bb;
    background-image: url(https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/logo.png);
    background-repeat: no-repeat;
    background-size: 56px 48.8px;
    background-position: 6px 20%;
}
</style>

## Benchmark
HTTP requests per second (Linux x64)

<div style="width: 100%;">
    <div align="center" style="width: auto;background-color: #0a0800; border-radius:10px; display: inline-grid;grid-template-columns: 100px 100px 100px 100px;  align-items: end;padding: 50px 30px;">
        <div style="--amount: 124943; --max: 150000" class="socketify graph-bar">
            <div class="graph-label">124,943</div>
            <div class="graph-label label-bottom">socketify PyPy3</div>
        </div>
        <div style="--amount: 70877; --max: 150000" class="socketify graph-bar">
            <div class="graph-label">70,877</div>
            <div class="graph-label label-bottom">socketify Python3</div>
        </div>
        <div style="--amount: 30173; --max: 150000" class="graph-bar">
            <div class="graph-label">30,173</div>
            <div class="graph-label label-bottom">gunicorn Python3</div>
        </div>
        <div style="--amount: 17580; --max: 150000" class="graph-bar">
            <div class="graph-label">17,580</div>
            <div class="graph-label label-bottom">gunicorn PyPy3</div>
        </div>
    </div>
</div>
<br/>
Runtime versions: PyPy3 7.3.9 and Python 3.10.7<br/>
Framework versions: gunicorn 20.1.0 + uvicorn 0.19.0, socketify alpha<br/>
Tested with ./http_load_test 40 127.0.0.1 8000 from [uSockets](https://github.com/uNetworking/uSockets)
Source code in [bench](https://github.com/cirospaciari/socketify.py/tree/main/bench)

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
