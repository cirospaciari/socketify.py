from wsgiref.simple_server import make_server

import falcon

class Home:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Hello, World!"


app = falcon.App()

home = Home()
app.add_route('/', home)

if __name__ == '__main__':
    with make_server('', 8000, app) as httpd:
        print('Serving on port 8000...')

        # Serve until process is killed
        httpd.serve_forever()

#pypy3 -m gunicorn falcon_plaintext:app -w 1 