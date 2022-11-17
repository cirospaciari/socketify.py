# App.get, post, options, delete, patch, put, head, connect, trace and any routes
You attach behavior to "URL routes". A function/lambda is paired with a "method" (Http method that is) and a pattern (the URL matching pattern).

Methods are many, but most common are probably get & post. They all have the same signature, let's look at one example:

```python
app.get("/", lambda res, req: res.end("Hello World!"))
```

```python
def home(res, req):
    res.end("Hello World!")

app.get("/", home)
```

```python
async def home(res, req):
    body = await res.get_json()
    user = await get_user(body)
    res.cork_end(f"Hello World! {user.name}")
    
app.post("/", home)
```
> Whenever your callback is a coroutine, such as the async/await, automatic corking can only happen in the very first portion of the coroutine (consider await a separator which essentially cuts the coroutine into smaller segments). Only the first "segment" of the coroutine will be called from socketify, the following async segments will be called by the asyncio event loop at a later point in time and will thus not be under our control with default corking enabled, HttpRequest object being stack-allocated and only valid in one single callback invocation so only valid in the first "segment" before the first await. If you just want to preserve headers, url, method, cookies and query string you can use `req.preserve()` to copy all data and keep it in the request object, but will be some performance penality. Take a look in [Corking](corking.md) for get a more in deph information

## Pattern matching
Routes are matched in order of specificity, not by the order you register them:

- Highest priority - static routes, think "/hello/this/is/static".
- Middle priority - parameter routes, think "/candy/:kind", where value of :kind is retrieved by `req.get_parameter(0)`.
- Lowest priority - wildcard routes, think "/hello/*".
In other words, the more specific a route is, the earlier it will match. This allows you to define wildcard routes that match a wide range of URLs and then "carve" out more specific behavior from that.

"any" routes, those who match any HTTP method, will match with lower priority than routes which specify their specific HTTP method (such as GET) if and only if the two routes otherwise are equally specific.

## Skipping to the next Route
If you want to tell to the router to go to the next route, you can call `req.set_yield(1)`

Example
```python
def user(res, req):
    try:
        if int(req.get_parameter(0)) == 1:
            return res.end("Hello user 1!")
    finally:
        # invalid user tells to go, to the next route valid route (not found)
        req.set_yield(1)


def not_found(res, req):
    res.write_status(404).end("Not Found")

app.get("/", home)
app.get("/user/:user_id", user)
app.any("/*", not_found)

```

## Error handler
In case of some uncaught exceptions we will always try our best to call the error handler, you can set the handler using `app.set_error_handler(hanlder)`

```python

def xablau(res, req):
    raise RuntimeError("Xablau!")


async def async_xablau(res, req):
    await asyncio.sleep(1)
    raise RuntimeError("Async Xablau!")


# this can be async no problems
def on_error(error, res, req):
    # here you can log properly the error and do a pretty response to your clients
    print("Somethind goes %s" % str(error))
    # response and request can be None if the error is in an async function
    if res != None:
        # if response exists try to send something
        res.write_status(500)
        res.end("Sorry we did something wrong")


app.get("/", xablau)
app.get("/async", async_xablau)
app.set_error_handler(on_error)
```

## Proxies

We implement `Proxy Protocol v2` so you can use `res.get_proxied_remote_address()` to get the proxied IP.

```python
from socketify import App


def home(res, req):
    res.write("<html><h1>")
    res.write("Your proxied IP is: %s" % res.get_proxied_remote_address())
    res.write("</h1><h1>")
    res.write("Your IP as seen by the origin server is: %s" % res.get_remote_address())
    res.end("</h1></html>")


app = App()
app.get("/*", home)
app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()
```

### Per-SNI HttpRouter Support

```python

def default(res, req):
    res.end("Hello from catch-all context!")

app.get("/*", default)

  
# Following is the context for *.google.* domain 
# PS: options are optional if you are not using SSL
app.add_server_name("*.google.*", AppOptions(key_file_name="./misc/key.pem", cert_file_name="./misc/cert.pem", passphrase="1234"))

def google(res, req):
    res.end("Hello from *.google.* context!")

app.domain("*.google.*").get("/*", google)

#you can also remove an server name
app.remove_server_name("*.google.*")

```

### Next [Middlewares](middlewares.md)