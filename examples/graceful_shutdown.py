from socketify import App, AppOptions, AppListenOptions

app = App()


def shutdown(res, req):
    res.end("Good bye!")
    app.close()


app.get("/", lambda res, req: res.end("Hello!"))
app.get("/shutdown", shutdown)


app.listen(
    3000,
    lambda config: print(
        "Listening on port http://localhost:%s now\n" % str(config.port)
    ),
)
app.run()
print("App Closed!")
