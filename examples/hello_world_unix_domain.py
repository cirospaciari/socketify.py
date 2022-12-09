from socketify import App, AppListenOptions

app = App()
app.get("/", lambda res, req: res.end("Hello World!"))
app.listen(
    AppListenOptions(domain="/tmp/test.sock"),
    lambda config: print("Listening on port %s http://localhost/ now\n" % config.domain),
)
app.run()

# you can test with curl -GET --unix-socket /tmp/test.sock http://localhost/