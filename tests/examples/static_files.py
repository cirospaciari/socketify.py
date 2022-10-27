from socketify import App
from helpers.static import static_route
from helpers.static import send_file


app = App()

#serve all files in public folder under / route (main route but can be like /assets)
static_route(app, "/", "./public")

#send home page index.html
async def home(res, req):
    #sends the whole file with 304 and bytes range support
    await send_file(res, req, "./public/index.html")
    
app.get("/", home)

app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()

