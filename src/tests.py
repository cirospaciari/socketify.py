from socketify import App
import asyncio 
app = App(lifespan=False)
router = app.router()

@app.on_start
async def on_start():
    print("wait...")
    await asyncio.sleep(1)
    print("start!")

@app.on_shutdown
async def on_shutdown():
    print("wait...")
    await asyncio.sleep(1)
    print("shutdown!")

@router.get("/")
def home(res, req, data=None):
    # print(data)
    # print("token", req.token)
    # cart = await req.get_cart()
    # print("cart", cart)
    # user = await req.get_user()
    # print("user", user)
    # print("token", req.token)
    res.send({"Hello": "World!"}, headers=(("X-Rate-Limit-Remaining", "10"), (b'Another-Headers', b'Value')))


app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()

