from socketify import App

app = App()
app.get("/", lambda res, req: res.end("Hello World!"))
app.listen(8000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()

# 124943.00 req/s socketify.py - PyPy3 7.3.9 
# 70877.75 req/s socketify.py - Python 3.10.7
# 30173.75 req/s gunicorn 20.1.0 + uvicorn 0.19.0 - Python 3.10.7
# 17580.25 req/s gunicorn 20.1.0 + uvicorn 0.19.0 - PyPy3 7.3.9 
#  8044.50 req/s flask 2.1.2 PyPy 7.3.9 
#  1957.50 req/s flask 2.1.2 Python 3.10.7
