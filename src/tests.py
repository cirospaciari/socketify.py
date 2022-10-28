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



# unsigned int uws_num_subscribers(int ssl, uws_app_t *app, const char *topic);
# bool uws_publish(int ssl, uws_app_t *app, const char *topic, size_t topic_length, const char *message, size_t message_length, uws_opcode_t opcode, bool compress);
# void *uws_get_native_handle(int ssl, uws_app_t *app);
# void uws_remove_server_name(int ssl, uws_app_t *app, const char *hostname_pattern);
# void uws_add_server_name(int ssl, uws_app_t *app, const char *hostname_pattern);
# void uws_add_server_name_with_options(int ssl, uws_app_t *app, const char *hostname_pattern, struct us_socket_context_options_t options);
# void uws_missing_server_name(int ssl, uws_app_t *app, uws_missing_server_handler handler, void *user_data);
# void uws_filter(int ssl, uws_app_t *app, uws_filter_handler handler, void *user_data);

# https://github.com/uNetworking/uWebSockets.js/blob/master/examples/VideoStreamer.js
from socketify import App
# import os
import multiprocessing
import asyncio
import time
import mimetypes
mimetypes.init()

#need to fix get_data using sel._data etc
async def home(res, req):
    print("full", req.get_full_url())
    print("normal", req.get_url())

    req.for_each_header(lambda key,value: print("Header %s: %s" % (key, value)))
    res.end("Test")

def run_app():
    app = App()    
    app.get("/", home)
    app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % (config.port)))
    app.run()

def create_fork():
    n = os.fork()
    # n greater than 0 means parent process
    if not n > 0:
        run_app()

# # fork limiting the cpu count - 1
# for i in range(1, multiprocessing.cpu_count()):
#     create_fork()

run_app() # run app on the main process too :)
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

#git submodule sync