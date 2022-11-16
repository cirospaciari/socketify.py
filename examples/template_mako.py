from socketify import App
#see helper/templates.py for plugin implementation
from helpers.templates import MakoTemplate


app = App()
app.template(MakoTemplate(directories=['./templates'], output_encoding='utf-8', encoding_errors='replace'))

def home(res, req):
    res.render("mako_home.html", message="Hello, World")

app.get("/", home)
app.listen(3000, lambda config: print("Listening on port http://localhost:%s now\n" % str(config.port)))
app.run()