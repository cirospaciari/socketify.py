from socketify import App

# this is just an example of implementation you can just import using from socketify import middleware for an more complete version


def middleware(*functions):
    def middleware_route(res, req):
        data = None
        # cicle to all middlewares
        for function in functions:
            # call middlewares
            data = function(res, req, data)
            # stops if returns Falsy
            if not data:
                break

    return middleware_route


def get_user(authorization_header):
    if authorization_header:
        return {"greeting": "Hello, World"}
    return None


def auth(res, req, data=None):
    user = get_user(req.get_header("authorization"))
    if not user:
        res.write_status(403).end("not authorized")
        return False

    # returns extra data
    return user


def home(res, req, user=None):
    res.end(user.get("greeting", None))


app = App()
app.get("/", middleware(auth, home))
app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()
