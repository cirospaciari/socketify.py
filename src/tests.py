from socketify.template import *

# https://github.com/chtd/psycopg2cffi/
# https://github.com/tlocke/pg8000
# https://www.psycopg.org/docs/advanced.html#asynchronous-support (works in cffi version too)
# https://github.com/sass/libsass-python

# @memo() # generate an static string after first execution aka skipping re-rendering when props are unchanged 
# def title(message):
#     return h1(message, classes="title-light")

# @memo(maxsize=128)
def htemplate(message, left_message, right_message):

    return (
        h1(message),
        span(
            children=(
                span(left_message, classes=("text-light", "align-left")),
                span(right_message, classes=("text-light", "align-right")),
            ),
        ),
    )


# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta http-equiv="X-UA-Compatible" content="IE=edge">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Document</title>
# </head>
# <body>
# </body>
# </html>
def html5():
    return (
        doctype(),
        html(lang="en", children=(
            head(children=(
                # meta(charset="UTF-8")
                # meta(http_equiv="X-UA-Compatible",content="IE=edge")
                # meta(name="vieport",content="width=device-width, initial-scale=1.0")
                title("Document")
            )),
            body()
        ))
    )

# print(render_tostring(html5()))
# from mako.template import Template

# template = Template(
#     "<h1>${message}</h1><span><span classes=\"text-light align-left\">${left_message}</span><span classes=\"text-light align-right\">${right_message}</span></span>"
# )

# from jinja2 import Environment, BaseLoader
# rtemplate = Environment(loader=BaseLoader()).from_string("<h1>{{ message }}</h1><span><span classes=\"text-light align-left\">{{ left_message }}</span><span classes=\"text-light align-right\">{{ right_message }}</span></span>")

# print(
#     render_tostring(htemplate(
#         message="Hello, World!",
#         left_message="Text in Left",
#         right_message="Text in Right",
#     ))
# )
# print(
#     render_tostring(htemplate(
#         message="Hello, World!",
#         left_message="Text in Left",
#         right_message="Text in Right",
#     ))
# )

# for i in range(1_000_000):
#     render_tostring(htemplate(message="Hello, World!", left_message="Text in Left", right_message="Text in Right"))
    # template.render(message="Hello, World!", left_message="Text in Left", right_message="Text in Right")
    # rtemplate.render(message="Hello, World!", left_message="Text in Left", right_message="Text in Right")

# print(
#     render(
#         html(
#             message="Hello, World!",
#             left_message="Text in Left",
#             right_message="Text in Right",
#         )
#     )
# )
