from socketify import App, AppOptions, AppListenOptions
import asyncio

app = App()

def xablau(res, req):
    raise RuntimeError("Xablau!")

async def async_xablau(res, req):
    await asyncio.sleep(1)
    raise RuntimeError("Async Xablau!")

#this can be async no problems 
def on_error(error, res, req): 
    #here you can log properly the error and doa  pretty response to your clients
    print("Somethind goes %s" % str(error))
    #response and request can be None if the error is in an async function
    if res != None:
        res.write_status(500)
        res.end("Sorry we did something wrong")

app.get("/", xablau)
app.get("/async", async_xablau)

app.set_error_handler(on_error)

app.listen(3000, lambda config: print("Listening on port http://localhost:%s now\n" % str(config.port)))
app.run()