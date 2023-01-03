from socketify import App

app = App()

def extension(request, response, ws):

    @request.method
    async def get_user(self):
        token = self.get_header("token")
        self.token = token
        return { "name": "Test" } if token else { "name", "Anonymous" }

    @request.method
    async def get_cart(self):
        return [{ "quantity": 10, "name": "T-Shirt" }]

    request.property("token", None)

app.register(extension)

app.get("/", lambda res, req: res.end("Hello World!"))
app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()
