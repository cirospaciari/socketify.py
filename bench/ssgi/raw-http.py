from socketify import SSGI

class Application:
    def get_supported(self, supported_interfaces):

        def ssgi(type, method, path, query_string, get_header, res):
            # if type == "http":
            res.send(b'Hello, World!')
            # else:
            #     res.reject() # reject websocket connections

        return {
            "http": ("ssgi" if supported_interfaces.get("ssgi", None) else None, ssgi),
            # "websocket": ("ssgi" if supported_interfaces.get("ssgi", None) else None, ssgi)
        }


app = Application()

if __name__ == "__main__":
    SSGI(app).listen(8000, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()

# python3 -m gunicorn test:app -w 1 -k uvicorn.workers.UvicornWorker