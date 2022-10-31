from socketify import App
import os
import multiprocessing

def run_app():
    app = App()
    app.get("/", lambda res, req: res.end("Hello, World!"))
    app.listen(3000, lambda config: print("PID %d Listening on port http://localhost:%d now\n" % (os.getpid(), config.port)))
    app.run()

def create_fork():
    n = os.fork()
    # n greater than 0 means parent process
    if not n > 0:
        run_app()

# fork limiting the cpu count - 1
for i in range(1, multiprocessing.cpu_count()):
    create_fork()

run_app() # run app on the main process too :)