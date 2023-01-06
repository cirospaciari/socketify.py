import falcon.asgi
from socketify import ASGI


class Home:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Hello, World!"
    async def on_post(self, req, resp):
        # curl -d '{"name":"test"}' -H "Content-Type: application/json" -X POST http://localhost:8000/
        json = await req.media
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = json.get("name", "")
        
        


app = falcon.asgi.App()

home = Home()
app.add_route("/", home)

if __name__ == "__main__":
    ASGI(app).listen(8000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run(workers=8)
