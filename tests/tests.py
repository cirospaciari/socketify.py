import threading
from datetime import datetime
import time
import os
import asyncio
#import uvloop
from json import dumps as json
from socketify import App, AppOptions, AppListenOptions
# from ujson import dumps as json
# from zzzjson import stringify as json #is too slow with CFFI
# from orjson import dumps
# def json(data):
#     return dumps(data).decode("utf-8")
# from rapidjson import dumps as json

# import cysimdjson
# parser = cysimdjson.JSONParser()


# def parse(value):
#     return parser.loads(value)

# def json(value):
#     if isinstance(value, dict):
#         for key in value:
#             return "{\"%s\":\"%s\"}" % (key, value[key])
            
    #only supports dict
    # return None


current_http_date = datetime.utcnow().isoformat() + "Z"
stopped = False
def time_thread():
    while not stopped:
        global current_http_date
        current_http_date = datetime.utcnow().isoformat() + "Z"
        time.sleep(1)

def plaintext(res, req):
    res.write_header("Date", current_http_date)
    res.write_header("Server", "socketify")
    res.write_header("Content-Type", "text/plain")
    res.end("Hello, World!")

def applicationjson(res, req):
    res.write_header("Date", current_http_date)
    res.write_header("Server", "socketify")
    res.write_header("Content-Type", "application/json")
    res.end(json({"message":"Hello, World!"}))


def async_route(handler):
    return lambda res,req: asyncio.run(handler(res, req))

async def plaintext_async(res, req):
    # await asyncio.sleep(1)
    res.write_header("Date", current_http_date)
    res.write_header("Server", "socketify")
    res.write_header("Content-Type", "text/plain")
    res.end("Hello, World!")   

async def test():
    await asyncio.sleep(1)
    print("Hello!")

def run_app():
    timing = threading.Thread(target=time_thread, args=())
    timing.start()
    app = App(AppOptions(key_file_name="./misc/key.pem", cert_file_name="./misc/cert.pem", passphrase="1234"))
    app.get("/", plaintext)
    # app.get("/json", applicationjson)
    # app.get("/plaintext", plaintext)
    # app.get("/", async_route(plaintext_async))
    app.listen(3000, lambda config: print("Listening on port http://localhost:%s now\n" % str(config.port)))
    # app.listen(AppListenOptions(port=3000, host="0.0.0.0"), lambda config: print("Listening on port http://%s:%d now\n" % (config.host, config.port)))
    
    # loop = uvloop.new_event_loop()
    # asyncio.set_event_loop(loop)
    # print(loop)
    # asyncio.run(test())
    app.run()
    
    # app.run()
    # asyncio.get_event_loop().run_forever()
def create_fork():
    n = os.fork()
    # n greater than 0 means parent process
    if not n > 0:
        run_app()

# for index in range(3):
#     create_fork()

# async def main():
#     print('Hello ...')
#     await asyncio.sleep(1)
#     print('... World!')

# asyncio.run(main())
# asyncio.get_event_loop().run_forever()

run_app()


# print(parse("{\"message\":\"Hello, World\"}")["message"])
# print(json({ "array": [1, 5.5, True, False, None, "{\"message\":\"Hello, World\"}"], "yes": True, "nop": False, "none": None, "int": 1, "float": 5.5, "e": 1.2123123123123124e+37, "string": "{\"message\":\"Hello, World\"}" }))

# print(json(AppOptions(key_file_name="./misc/key.pem", cert_file_name="./misc/cert.pem", passphrase="1234").__dict__))

#pip install git+https://github.com/inducer/pycuda.git (submodules are cloned recursively)
#https://stackoverflow.com/questions/1754966/how-can-i-run-a-makefile-in-setup-py
#https://packaging.python.org/en/latest/tutorials/packaging-projects/
#pypy3 -m pip install uvloop (not working with pypy)
#apt install pypy3-dev
#pypy3 -m pip install ujson (its slow D=)
#pypy3 -m pip install orjson (dont support pypy)
#pypy3 -m pip install cysimdjson (uses simdjson) is parse only
#pypy3 -m pip install rapidjson (not working with pypy)
#https://github.com/MagicStack/uvloop/issues/380
#https://foss.heptapod.net/pypy/pypy/-/issues/3740


#git submodule update --init --recursive --remote
#pypy3 -m pip install --upgrade build
#pypy3 -m build
#pypy3 -m pip install .
#pypy3 -m pip uninstall socketify