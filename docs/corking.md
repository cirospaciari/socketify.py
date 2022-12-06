## Corking
It is very important to understand the corking mechanism, as that is responsible for efficiently formatting, packing and sending data. Without corking your app will still work reliably, but can perform very bad and use excessive networking. In some cases the performance can be dreadful without proper corking.

That's why your sockets will be corked by default in most simple cases, including all of the examples provided. However there are cases where default corking cannot happen automatically.

Whenever your registered business logic (your callbacks) are called from the library, such as when receiving a message or when a socket opens, you'll be corked by default. Whatever you do with the socket inside of that callback will be efficient and properly corked.

If you have callbacks registered to some other library, say libhiredis, those callbacks will not be called with corked sockets (how could we know when to cork the socket if we don't control the third-party library!?).

Only one single socket can be corked at any point in time (isolated per thread, of course). It is efficient to cork-and-uncork.

Whenever your callback is a coroutine, such as the async/await, automatic corking can only happen in the very first portion of the coroutine (consider await a separator which essentially cuts the coroutine into smaller segments). Only the first "segment" of the coroutine will be called from socketify, the following async segments will be called by the asyncio event loop at a later point in time and will thus not be under our control with default corking enabled, HttpRequest object being stack-allocated and only valid in one single callback invocation so only valid in the first "segment" before the first await.
If you just want to preserve headers, url, method, cookies and query string you can use `req.preserve()` to copy all data and keep it in the request object, but will be some performance penalty.

Corking is important even for calls which seem to be "atomic" and only send one chunk. res.end, res.try_end, res.write_status, res.write_header will most likely send multiple chunks of data and is very important to properly cork.

You can make sure corking is enabled, even for cases where default corking would be enabled, by wrapping whatever sending function calls in a lambda or function like so:
```python
async def home(res, req):
    auth = req.get_header("authorization")
    user = await do_auth(auth)
    
    res.cork(lambda res: res.end(f"Hello {user.name}"))
```

```python
async def home(res, req):
    auth = req.get_header("authorization")
    user = await do_auth(auth)

    def on_cork(res):
        res.write_header("session_id", user.session_id)
        res.end(f"Hello {user.name}")
    
    res.cork(on_cork)
```
> You cannot use async inside cork but, you can cork only when you need to send the response after all the async happens

For convenience we have `res.cork_end()`, `ws.cork_send()` that will cork and call end for you, and also `res.render()` that will always response using `res.cork_end()` to send your HTML / Data

### Next [Routes](routes.md)