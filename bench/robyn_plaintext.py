from robyn import Robyn

app = Robyn(__file__)


@app.get("/")
async def h(request):
    return "Hello, world!"


app.start(port=8000)

# python3 ./robyn_plaintext.py --processes 4 --log-level CRITICAL
# pypy3 did not compile
