from socketify import App, AppOptions, AppListenOptions
import asyncio

app = App()

async def delayed_hello(delay, res):
    await asyncio.sleep(delay) #do something async
    res.cork_end("Hello with delay!")

def home(res, req):
    #request object only lives during the life time of this call
    #get parameters, query, headers anything you need here
    delay = req.get_query("delay")
    delay = 0 if delay == None else float(delay)
    #tell response to run this in the event loop
    #abort handler is grabed here, so responses only will be send if res.aborted == False
    res.run_async(delayed_hello(delay, res))

async def json(res, req):
    #request object only lives during the life time of this call
    #get parameters, query, headers anything you need here before first await :)
    user_agent = req.get_header("user-agent")
    #req maybe will not be available in direct attached async functions after await
    await asyncio.sleep(2) #do something async
    
    res.cork_end({ "message": "I'm delayed!", "user-agent": user_agent})

def not_found(res, req):
    res.write_status(404).end("Not Found")

app.get("/", home)
app.get("/json", json)
app.any("/*", not_found)

app.listen(3000, lambda config: print("Listening on port http://localhost:%s now\n" % str(config.port)))

app.run()