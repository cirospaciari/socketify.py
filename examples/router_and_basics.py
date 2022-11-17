from socketify import App, AppOptions, AppListenOptions
import asyncio
from datetime import datetime, timedelta

app = App()


def home(res, req):
    res.end("Hello :)")


def anything(res, req):
    res.end("Any route with method: %s" % req.get_method())


def cookies(res, req):
    # cookies are writen after end
    res.set_cookie(
        "spaciari",
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


def useragent(res, req):
    res.end("Your user agent is: %s" % req.get_header("user-agent"))


def user(res, req):
    try:
        if int(req.get_parameter(0)) == 1:
            return res.end("Hello user with id 1!")
        # get_parameters returns an array of parameters
        # params = req.get_parameters()

    finally:
        # invalid user tells to go, to the next route valid route (not found)
        req.set_yield(1)


async def delayed_hello(delay, res):
    await asyncio.sleep(delay)  # do something async
    res.cork_end("Hello sorry for the delay!")
    # cork_end is a less verbose way of writing
    # res.cork(lambda res: res.end("Hello sorry for the delay!"))


def delayed(res, req):
    # request object only lives during the life time of this call
    # get parameters, query, headers anything you need here
    delay = req.get_query("delay")
    delay = 1 if delay == None else float(delay)

    # get queries returns an dict with all query string
    # queries = req.get_queries()

    # tell response to run this in the event loop
    # abort handler is grabed here, so responses only will be send if res.aborted == False
    res.run_async(delayed_hello(delay, res))


def json(res, req):
    # if you pass an object will auto write an header with application/json
    res.end({"message": "I'm an application/json!"})


async def sleepy_json(res, req):
    # get parameters, query, headers anything you need here before first await :)
    user_agent = req.get_header("user-agent")
    # print all headers
    req.for_each_header(lambda key, value: print("Header %s: %s" % (key, value)))
    # or if you want get all headers in an dict
    print("All headers", req.get_headers())

    # req maybe will not be available in direct attached async functions after await
    # but if you dont care about req info you can do it
    await asyncio.sleep(2)  # do something async
    res.cork_end({"message": "I'm delayed!", "user-agent": user_agent})


def custom_header(res, req):
    res.write_header("Content-Type", "application/octet-stream")
    res.write_header("Content-Disposition", 'attachment; filename="message.txt"')
    res.end("Downloaded this ;)")


def send_in_parts(res, req):
    # write and end accepts bytes and str or its try to dumps to an json
    res.write("I can")
    res.write(" send ")
    res.write("messages")
    res.end(" in parts!")


def redirect(res, req):
    # status code is optional default is 302
    res.redirect("/redirected", 302)


def redirected(res, req):
    res.end("You got redirected to here :D")


def not_found(res, req):
    res.write_status(404).end("Not Found")


# app.any, app.get, app.put, app.post, app.head, app.options, app.delete, app.patch, app.connect and app.trace are available
app.get("/", home)
app.any("/anything", anything)
app.get("/user/agent", useragent)
app.get("/user/:id", user)
app.get("/delayed", delayed)
app.get("/json", json)
app.get("/sleepy", sleepy_json)
app.get("/custom_header", custom_header)
app.get("/cookies", cookies)
app.get("/send_in_parts", send_in_parts)
app.get("/redirect", redirect)
app.get("/redirected", redirected)
# too see about app.post go to ./upload_or_post.py :D
# Wildcard at last always :)
app.any("/*", not_found)

app.listen(
    3000,
    lambda config: print(
        "Listening on port http://localhost:%s now\n" % str(config.port)
    ),
)
app.run()
