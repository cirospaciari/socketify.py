# This example just show how to use python logging to log requests

from socketify import App
import logging
# Setup log format
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO
)

# simply devlog high-order function, you can also create an middleware to use logging, see middleware_router.py and middleware.py
def devlog(handler):
    def devlog_route(res, req):
        logging.info(f'{req.get_method()} {req.get_full_url()} {req.get_headers()=}')
        handler(res, req)
    return devlog_route

# Now is just use the devlog function or middleware

app = App()

def home(res, req):
    res.end("Hello World!")

app.get("/", devlog(home))

app.listen(
    3000,
    lambda config: logging.info("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()


