# Middlewares

We have support to middlewares using the `middleware` helper function and the `MiddlewareRouter`.
Like said in [routes](routes.md) and [corking](corking.md) section Whenever your callback is a coroutine, such as the async/await, automatic corking can only happen in the very first portion of the coroutine (consider await a separator which essentially cuts the coroutine into smaller segments). Only the first "segment" of the coroutine will be called from socketify, the following async segments will be called by the asyncio event loop at a later point in time and will thus not be under our control with default corking enabled. HttpRequest object being stack-allocated and only valid in one single callback invocation so only valid in the first "segment" before the first await.

In case of middlewares if one of them is an coroutine, we automatically call `req.preserve()` to preserve request data between middlewares.
Middlewares are executed in series, so if returned data is Falsy (False/None etc) will result in the end of the execution, if is not Falsy the data will pass to the next middleware like an third parameter.



```python
from socketify import App, MiddlewareRouter, middleware


async def get_user(authorization):
    if authorization:
        # you can do something async here
        return {"greeting": "Hello, World"}
    return None


async def auth(res, req, data=None):
    user = await get_user(req.get_header("authorization"))
    if not user:
        res.write_status(403).end("not authorized")
        # returning Falsy in middlewares just stop the execution of the next middleware
        return False

    # returns extra data
    return user


def another_middie(res, req, data=None):
    # now we can mix sync and async and change the data here
    if isinstance(data, dict):
        gretting = data.get("greeting", "")
        data["greeting"] = f"{gretting} from another middie ;)"
    return data


def home(res, req, user=None):
    res.cork_end(user.get("greeting", None))


app = App()

#you can use middleware directly on the default router
app.get('/direct',  middleware(auth, another_middie, home))

# you can use an Middleware router to add middlewares to every route you set
auth_router = MiddlewareRouter(app, auth)
auth_router.get("/", home)
# you can also mix middleware() with MiddlewareRouter
auth_router.get("/another", middleware(another_middie, home))

# you can also pass multiple middlewares on the MiddlewareRouter
other_router = MiddlewareRouter(app, auth, another_middie)
other_router.get("/another_way", home)


app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()

```