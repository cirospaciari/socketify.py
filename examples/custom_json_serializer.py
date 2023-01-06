from socketify import App
import ujson

app = App()


# set json serializer to ujson
# json serializer must have dumps and loads functions
app.json_serializer(ujson)

app.get("/", lambda res, req: res.end({"Hello":"World!"}))
app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()
