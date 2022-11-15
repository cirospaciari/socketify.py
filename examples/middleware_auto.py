from socketify import App
import inspect

def middleware(*functions):
    async def middleware_route(res, req):
        data = None
        some_async_as_run = False
        #cicle to all middlewares
        for function in functions:
            #detect if is coroutine or not
            if inspect.iscoroutinefunction(function):
                #in async query string, arguments and headers are only valid until the first await
                if not some_async_as_run:
                     #get_headers will preserve headers (and cookies) inside req, after await
                    headers = req.get_headers() 
                    #get_parameters will preserve all params inside req after await 
                    params = req.get_parameters()
                    #get queries will preserve all queries inside req after await 
                    queries = req.get_queries()
                    #mark to only grab header, params and queries one time
                    some_async_as_run = True 
                data = await function(res, req, data)
            else:
                #call middlewares
                data = function(res, req, data)
                #stops if returns Falsy
                if not data:
                    break

    return middleware_route
    
async def get_user(authorization):
    if authorization:
        #you can do something async here
        return { 'greeting': 'Hello, World' }
    return None

async def auth(res, req, data=None):
    user = await get_user(req.get_header('authorization'))
    if not user: 
        res.write_status(403).end("not authorized")
        return False

    #returns extra data
    return user

def another_middie(res, req, data=None):
    #now we can mix sync and async and change the data here
    if isinstance(data, dict):
        gretting = data.get('greeting', '')
        data['greeting'] = f"{gretting} from another middie ;)"
    return data

def home(res, req, user=None):
    res.end(user.get('greeting', None))

app = App()
app.get("/", middleware(auth, another_middie, home))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()