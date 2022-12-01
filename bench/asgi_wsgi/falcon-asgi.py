import falcon.asgi
from socketify import ASGI


class Home:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Hello, World!"
    async def on_post(self, req, resp):
        raw_data = await req.stream.read()
        print("data", raw_data)
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = raw_data
        
        


app = falcon.asgi.App()

home = Home()
app.add_route("/", home)

if __name__ == "__main__":
    ASGI(app).listen(8000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()
   
#pypy3 -m gunicorn uvicorn_guvicorn_plaintext:app -w 1 -k uvicorn.workers.UvicornWorker