from wsgiref.simple_server import make_server

import falcon


class Home:
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200  # This is the default status
        resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
        resp.text = "Hello, World!"


app = falcon.App()

home = Home()
app.add_route("/", home)

if __name__ == "__main__":
    with make_server("", 8000, app) as httpd:
        print("Serving on port 8000...")

        # Serve until process is killed
        httpd.serve_forever()

# pypy3 -m gunicorn falcon_plaintext:app -w 4 --worker-class=gevent #recomended for pypy3
# python3 -m gunicorn falcon_plaintext:app -w 4 #without Cython
# pypy3 -m gunicorn falcon_plaintext:app -w 4 #without gevent
# python3 -m gunicorn falcon_plaintext:app -w 4 --worker-class="egg:meinheld#gunicorn_worker" #with Cython
# meinheld is buggy -> greenlet.c:566:10: error: no member named 'use_tracing' in 'struct _ts'
# so using pip3 install git+https://github.com/idot/meinheld.git@2bfe452d6608c92688d92337c87b1dd6448f4ccb
