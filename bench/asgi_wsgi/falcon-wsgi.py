import falcon.asgi
from socketify import WSGI


class Home:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Hello, World!"
    def on_post(self, req, resp):
        raw_data = req.stream.getvalue()
        print("data", raw_data)
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = raw_data
        
        


app = falcon.App()

home = Home()
app.add_route("/", home)

if __name__ == "__main__":
    WSGI(app).listen(8000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run(workers=8)