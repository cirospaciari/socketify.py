## All Basic Stuff

This section is to show the basics of `AppResponse` and `AppRequest`

### Writing data

`res.write(message)` were message can be String, bytes or an Object that can be converted to json, send the message to the response without ending.

`res.cork_end(message, end_connection=False)` or `res.end(message, end_connection=False)` were message can be String, bytes or an Object that can be converted to json, send the message to the response and end the response.

The above `res.end()` or `res.cork_end()` call will actually call three separate send functions; res.write_status, res.write_header and whatever it does itself. By wrapping the call in `res.cork` or `res.cork_end` you make sure these three send functions are efficient and only result in one single send syscall and one single SSL block if using SSL.


`res.send(message, content_type=b'text/plain, status=b'200 OK', headers=None, end_connection=False)` and `res.cork_send(message, content_type=b'text/plain', status=b'200 OK', headers=None, end_connection=False)`
combines `res.write_status()`, `res.write_headers()`, and `res.end()` in a way that is easier to use, if you want to send all in one call just using named parameters. Headers can receive any iterator of iterators/tuple like `iter(tuple(str, str))` where the first value is the header name and the following the value, using `res.cork_send` will make sure to send all the
data in a corked state.
    

Using `res.write_continue()` writes HTTP/1.1 100 Continue as response


`res.write_offset(offset)` sets the offset for writing data

`res.get_write_offset()` gets the current write offset

`res.pause()` and `res.resume()` pause and resume the response

```python
def send_in_parts(res, req):
    # write and end accepts bytes and str or its try to dumps to an json
    res.write("I can")
    res.write(" send ")
    res.write("messages")
    res.end(" in parts!")
    
```

### Ending without body
```python
def empty(res, req):
    res.end_without_body()
```

## Check if already responded
`res.has_responded()` returns True if the response is already done.

### Redirecting
```python
def redirect(res, req):
    # status code is optional default is 302
    res.redirect("/redirected", 302)

```

### Writing Status
```python
def not_found(res, req):
    res.write_status(404).end("Not Found")

def ok(res, req):
    res.write_status("200 OK").end("OK")
```

### Using send
```python
def not_found(res, req):
    res.send("Not Found", status=404)

def ok(res, req):
    res.send("OK", status="200 OK")

def json(res, req):
    res.send({"Hello", "World!"})

def with_headers(res, req):
    res.send({"Hello": "World!"}, headers=(("X-Rate-Limit-Remaining", "10"), (b'Another-Headers', b'Value')))
```


### Check the URL or Method
`req.get_full_url()` will return the path with query string
`req.get_url()` will return the path without query string
`req.get_method()` will return the HTTP Method (is case sensitive)

### Parameters
You can use `req.get_parameters(index)` to get the parametervalue as String or use `req.get_parameters()` to get an list of parameters

```python
def user(res, req):
    if int(req.get_parameter(0)) == 1:
            return res.end("Hello user with id 1!")
    params = req.get_parameters()
    print('All params', params)

app.get("/user/:id", user)
```

### Headers
You can use `req.get_header(lowercase_header_name)` to get the header string value as String or use `req.get_headers()` to get as a dict, `req.for_each_header()` if you just want to iterate in the headers. 
You can also set the header using `res.write_header(name, value)`.

```python
def home(res, req):
    auth = req.get_header("authorization")
    headers = req.get_headers()
    print("All headers", headers)

def custom_header(res, req):
    res.write_header("Content-Type", "application/octet-stream")
    res.write_header("Content-Disposition", 'attachment; filename="message.txt"')
    res.end("Downloaded this ;)")

def list_headers(res, req):
    req.for_each_header(lambda key, value: print("Header %s: %s" % (key, value)))

```

### Query String
You can use `req.get_query(parameter_name)` to get the query string value as String or use `req.get_queries()` to get as a dict.

```python
def home(res, req):
    search = req.get_query("search")
    
    queries = req.get_queries()
    print("All queries", queries)
```

### Cookies

We also have an `req.get_cookie(cookie_name)` to get a cookie value as String and `res.set_cookie(name, value, options=None)` to set a cookie.

```python

def cookies(res, req):
    # cookies are written after end
    res.set_cookie(
        "session_id",
        "1234567890",
        {
            # expires
            # path
            # comment
            # domain
            # max-age
            # secure
            # version
            # httponly
            # samesite
            "path": "/",
            # "domain": "*.test.com",
            "httponly": True,
            "samesite": "None",
            "secure": True,
            "expires": datetime.utcnow() + timedelta(minutes=30),
        },
    )
    res.end("Your session_id cookie is: %s" % req.get_cookie("session_id"))
```


## Getting remote address
You can get the remote address by using get_remote_address_bytes, get_remote_address and the proxied address using get_proxied_remote_address_bytes or get_proxied_remote_address

```python
def home(res, req):
    res.write("<html><h1>")
    res.write("Your proxied IP is: %s" % res.get_proxied_remote_address())
    res.write("</h1><h1>")
    res.write("Your IP as seen by the origin server is: %s" % res.get_remote_address())
    res.end("</h1></html>")
```
> The difference between the _bytes() version an non bytes is that one returns an String an the other the raw bytes


## App Pub/Sub
`app.num_subscribers(topic)` will return the number of subscribers at the topic.
`app.publish(topic, message, opcode=OpCode.BINARY, compress=False)` will send a message for everyone subscribed in the topic.


## Check if is aborted
If the connection aborted you can check `res.aborted` that will return True or False. You can also grab the abort handler, when using an async route, socketify will always auto grab the abort handler

```python
def home(res, req):
     def on_abort(res):
        res.aborted = True
        print("aborted!")
            
    res.on_aborted(on_abort)
```

## Running async from sync route
If you wanna to optimize a lot and don't use async without need you can use `res.run_async() or app.run_async()` to execute an coroutine

```python
from socketify import App, sendfile

def route_handler(res, req):
    if in_memory_text:
        res.end(in_memory_text)
    else:
        # grab the abort handler adding it to res.aborted if aborted
        res.grab_aborted_handler() 
        res.run_async(sendfile(res, req, "my_text"))
```


## Using ujson, orjson or any custom JSON serializer
socketify by default uses built-in `json` module with has great performance on PyPy, but if you wanna use another module instead of the default you can just register using `app.json_serializer(module)`

```python
from socketify import App
import ujson
app = App()

# set json serializer to ujson
# json serializer must have dumps and loads functions
app.json_serializer(ujson)

app.get("/", lambda res, req: res.end({"Hello":"World!"}))
```

## Raw socket pointer

If for some reason you need the raw socket pointer you can use `res.get_native_handle()` and will get an CFFI handler.

## Raw event loop pointer

If you need to access the raw pointer of `libuv` you can use `app.get_native_handle()` and will get an CFFI handler.

## Preserve data for use after await
HttpRequest object being stack-allocated and only valid in one single callback invocation so only valid in the first "segment" before the first await. 
If you just want to preserve headers, url, method, cookies and query string you can use `req.preserve()` to copy all data and keep it in the request object, but will be some performance penalty.

### Next [Upload and Post](upload-post.md)