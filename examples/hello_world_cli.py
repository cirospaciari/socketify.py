from socketify import App

# App will be created by the cli with all things you want configured
def run(app: App): 
    # add your routes here
    app.get("/", lambda res, req: res.end("Hello World!"))
    
# python -m socketify hello_world_cli:run --port 8080 --workers 2
# python3 -m socketify hello_world_cli:run --port 8080 --workers 2
# pypy3 -m socketify hello_world_cli:run --port 8080 --workers 2

# see options in with: python3 -m socketify --help