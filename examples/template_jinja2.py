from socketify import App
#see helper/templates.py for plugin implementation
from helpers.templates import Jinja2Template


app = App()
app.template(Jinja2Template("./templates", encoding='utf-8', followlinks=False))

def home(res, req):
    res.render("jinja2_home.html", title="Hello", message="Hello, World")

app.get("/", home)
app.listen(3000, lambda config: print("Listening on port http://localhost:%s now\n" % str(config.port)))
app.run()