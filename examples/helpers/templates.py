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
