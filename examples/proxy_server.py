from socketify import App, Response, Request

app = App()

router = app.router()

@router.connect("/")
def proxy_connect(res: Response, req: Request):
    print(req.get_url())

    res.send("Xablau")


app.listen(
    54321,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()
