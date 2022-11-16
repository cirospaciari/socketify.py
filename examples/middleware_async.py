from socketify import App

# this is just an example of implementation you can just import using from socketify import middleware for an more complete version


async def get_user(authorization):
    if authorization:
        # do actually something async here
        return {"greeting": "Hello, World"}
    return None


def auth(route):
    # in async query string, arguments and headers are only valid until the first await
    async def auth_middleware(res, req):
        # get_headers will preserve headers (and cookies) inside req, after await
        headers = req.get_headers()
        # get_parameters will preserve all params inside req after await
        params = req.get_parameters()
        # get queries will preserve all queries inside req after await
        queries = req.get_queries()

        user = await get_user(headers.get("authorization", None))
        if user:
            return route(res, req, user)

        return res.write_status(403).cork_end("not authorized")

    return auth_middleware


def home(res, req, user=None):
    theme = req.get_query("theme_color")
    theme = theme if theme else "light"
    greeting = user.get("greeting", None)
    user_id = req.get_parameter(0)
    res.cork_end(f"{greeting} <br/> theme: {theme} <br/> id: {user_id}")


app = App()
app.get("/user/:id", auth(home))
app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()


# curl --location --request GET 'http://localhost:3000/user/10?theme_color=dark' --header 'Authorization: Bearer 23456789'
