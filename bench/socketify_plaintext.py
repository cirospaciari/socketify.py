from socketify import App
import os
import multiprocessing
import asyncio
def run_app():
    app = App(request_response_factory_max_items=200_000)
    router = app.router()

    @router.get("/")
    def home(res, req):
        res.send(b"Hello, World!")
        
    app.listen(
        8000,
        lambda config: print(
            "PID %d Listening on port http://localhost:%d now\n"
            % (os.getpid(), config.port)
        ),
    )
    app.run()


def create_fork():
    n = os.fork()
    # n greater than 0 means parent process
    if not n > 0:
        run_app()


# fork limiting the cpu count - 1
for i in range(1, multiprocessing.cpu_count()):
    create_fork()

run_app()  # run app on the main process too :)
