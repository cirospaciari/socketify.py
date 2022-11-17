## Template Engines
Is very easy to add support to Template Engines, we already add `Mako` and `Jinja2` in /src/examples/helpers/templates.py.

### Implementation of Template extension:
```python
# Simple example of mako and jinja2 template plugin for socketify.py
from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions


from jinja2 import Environment, FileSystemLoader


class Jinja2Template:
    def __init__(self, searchpath, encoding="utf-8", followlinks=False):
        self.env = Environment(
            loader=FileSystemLoader(searchpath, encoding, followlinks)
        )

    # You can also add caching and logging strategy here if you want ;)
    def render(self, templatename, **kwargs):
        try:
            template = self.env.get_template(templatename)
            return template.render(**kwargs)
        except Exception as err:
            return str(err)


class MakoTemplate:
    def __init__(self, **options):
        self.lookup = TemplateLookup(**options)

    # You can also add caching and logging strategy here if you want ;)
    def render(self, templatename, **kwargs):
        try:
            template = self.lookup.get_template(templatename)
            return template.render(**kwargs)
        except Exception as err:
            return exceptions.html_error_template().render()
```

### Using templates
`app.template(instance)` will register the Template extension and call it when you use `res.render(...)`

```python
from socketify import App
# see helper/templates.py for plugin implementation
from helpers.templates import MakoTemplate


app = App()
# register templates
app.template(
    MakoTemplate(
        directories=["./templates"], output_encoding="utf-8", encoding_errors="replace"
    )
)


def home(res, req):
    res.render("mako_home.html", message="Hello, World")


app.get("/", home)
app.listen(
    3000,
    lambda config: print(
        "Listening on port http://localhost:%s now\n" % str(config.port)
    ),
)
app.run()

```

### Next [GraphiQL](graphiQL.md)