from socketify import App


async def get_user(authorization):
    if authorization:
        #do actually something async here
        return { 'greeting': 'Hello, World' }
    return None

def auth(home, queries=[]):
    #in async query string, arguments and headers are only valid until the first await
    async def auth_middleware(res, req):
        #get_headers will preserve headers (and cookies) after await
        headers = req.get_headers() 
        #get_parameters will preserve all params after await 
        params = req.get_parameters()

        #preserve desired query string data
        query_data = {}
        for query in queries:
            value = req.get_query(query)
            if value:
                query_data[query] = value

        user = await get_user(headers.get('authorization', None))
        if user:
            return home(res, req, user, query_data) 
        
        return res.write_status(403).cork_end("not authorized")
    
    return auth_middleware


def home(res, req, user=None, query={}):
    theme = query.get("theme_color", "light")
    greeting = user.get('greeting', None)
    user_id = req.get_parameter(0)
    res.cork_end(f"{greeting} <br/> theme: {theme} <br/> id: {user_id}")

app = App()
app.get("/user/:id", auth(home, ['theme_color']))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()


#curl --location --request GET 'http://localhost:3000/user/10?theme_color=dark' --header 'Authorization: Bearer 23456789'