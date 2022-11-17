## Sending Files and Serving Static Files
`app.static(route, path)` will serve all files in the directory as static, and will add byte range, 304, 404 support.
If you want to send a single file you can use `sendfile` helper for this. 

Example:
```python
from socketify import App, sendfile


app = App()


# send home page index.html
async def home(res, req):
    # sends the whole file with 304 and bytes range support
    await sendfile(res, req, "./public/index.html")


app.get("/", home)

# serve all files in public folder under /* route (you can use any route like /assets)
app.static("/", "./public")

app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()

```

### Next [Templates](templates.md)