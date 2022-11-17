from socketify import App, sendfile, CompressOptions, OpCode
import aiohttp
import json
from datetime import datetime, timedelta

app = App()
def get_welcome_message(room):
    return {
    "username": "@cirospaciari/socketify.py",
    "html_url": "https://www.github.com/cirospaciari/socketify.py",
    "avatar_url": "https://raw.githubusercontent.com/cirospaciari/socketify.py/main/misc/big_logo.png",
    "datetime": "",
    "name": "socketify.py",
    "text": f"Welcome to chat room #{room} :heart: be nice! :tada:"
}
RoomsHistory = {
    "general": [get_welcome_message("general")],
    "open-source": [get_welcome_message("open-source")],
    "reddit": [get_welcome_message("reddit")]
}

# send home page index.html
async def home(res, req):
    # Get Code for GitHub Auth
    code = req.get_query("code")
    if code is not None:
        try:
            # Get AccessToken for Auth
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": "9481803176fb73d616b7",
                        "client_secret": "???",
                        "code": code,
                    },
                    headers={"Accept": "application/json"},
                ) as response:
                    user = await response.json()
                    session = user.get("access_token", None)
                    res.set_cookie(
                        "session",
                        session,
                        {
                            "path": "/",
                            "httponly": False,
                            "expires": datetime.utcnow() + timedelta(minutes=30),
                        },
                    )
        except Exception as error:
            print(str(error))  # login fail

    # sends the whole file with 304 and bytes range support
    await sendfile(res, req, "./index.html")



async def ws_upgrade(res, req, socket_context):
    key = req.get_header("sec-websocket-key")
    protocol = req.get_header("sec-websocket-protocol")
    extensions = req.get_header("sec-websocket-extensions")
    token = req.get_query("token")
    room = req.get_query("room")
    if RoomsHistory.get(room, None) is None:
        return res.write_status(403).end("invalid room")

    try:
        async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://api.github.com/user",
                        headers={
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {token}",
                        },
                    ) as response:
                        user_data = await response.json()
                        if user_data.get('login', None) is not None:
                            user_data["room"] = room
                            res.upgrade(key, protocol, extensions, socket_context, user_data)
                        else:
                            res.write_status(403).end("auth fail")
    except Exception as error:
        print(str(error)) # auth error
        res.write_status(403).end("auth fail")
    

def ws_open(ws):
    user_data = ws.get_user_data()
    room = user_data.get("room", "general")
    ws.subscribe(room)

    history = RoomsHistory.get(room, [])
    if history:
        ws.send(history, OpCode.TEXT)

def ws_message(ws, message, opcode):
    try:
        message_data = json.loads(message)
        text = message_data.get('text', None)
        if text and len(text) < 1024 and message_data.get('datetime', None):
            user_data = ws.get_user_data()
            room = user_data.get("room", "general")
        
            message_data.update(user_data)
            history = RoomsHistory.get(room, [])
            if history:
                history.append(message_data)
                if len(history) > 100:
                    history = history[::100]
            
            #broadcast
            ws.send(message_data, OpCode.TEXT)
            ws.publish(room, message_data, OpCode.TEXT)

    except:
        pass

app.get("/", home)
# serve all files in assets folder under /assets/* route
app.static("/assets", "./assets")

app.ws(
    "/*",
    {
        "compression": CompressOptions.SHARED_COMPRESSOR,
        "max_payload_length": 64 * 1024,
        "idle_timeout": 60 * 30,
        "open": ws_open,
        "message": ws_message,
        "upgrade": ws_upgrade
    },
)
app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()
