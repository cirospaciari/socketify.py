# https://github.com/Tinche/aiofiles
# https://github.com/uNetworking/uWebSockets/issues/1426

# import os.path

# def in_directory(file, directory):
#     #make both absolute    
#     directory = os.path.join(os.path.realpath(directory), '')
#     file = os.path.realpath(file)

#     #return true, if the common prefix of both is equal to directory
#     #e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
#     return os.path.commonprefix([file, directory]) == directory

#  application/x-www-form-urlencoded 
#  application/x-www-form-urlencoded 
#  multipart/form-data 


from socketify import App
from datetime import datetime
from datetime import timedelta

async def home(res, req):
    data = await res.get_form_urlencoded()
    print(data)
    res.end(f"DATA! {data}")

app = App()
app.post("/", home)
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()

# from datetime import datetime
# raw = "_ga=GA1.1.1871393672.1649875681; affclick=null; __udf_j=d31b9af0d332fec181c1a893320322c0cb33ce95d7bdbd21a4cc4ee66d6d8c23817686b4ba59dd0e015cb95e8196157c"

# jar = Cookies(None)
# jar.set("session_id", "123132", {
#     "path": "/",
#     "domain": "*.test.com",
#     "httponly": True,
#     "expires": datetime.now()
# })
# print(jar.output())
# jar = cookies.SimpleCookie(raw)
# print(jar["_gaasasd"])
# print(split_header_words(raw))