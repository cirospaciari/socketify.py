import uws
import asyncio

# Integrate with asyncio
# asyncio.set_event_loop(uws.Loop())

app = uws.App()

def getHandler(res, req):
	res.end("Hello Python!")

app.get("/*", getHandler)

def listenHandler():
        print("Listening to port 3000")

app.listen(3000, listenHandler)
app.run()
# Run asyncio event loop
# asyncio.get_event_loop().run_forever()