# https://github.com/Tinche/aiofiles
# https://github.com/uNetworking/uWebSockets/issues/1426

# import os.path

    # DLL_EXPORT typedef void (*uws_listen_domain_handler)(struct us_listen_socket_t *listen_socket, const char* domain, size_t domain_length, int options, void *user_data);
    # DLL_EXPORT typedef void (*uws_missing_server_handler)(const char *hostname, size_t hostname_length, void *user_data);

# DLL_EXPORT void uws_app_listen_domain(int ssl, uws_app_t *app, const char *domain,size_t server_name_length, uws_listen_domain_handler handler, void *user_data);
    # DLL_EXPORT void uws_app_listen_domain_with_options(int ssl, uws_app_t *app, const char *domain,size_t server_name_length, int options, uws_listen_domain_handler handler, void *user_data);
    # DLL_EXPORT void uws_app_domain(int ssl, uws_app_t *app, const char* server_name, size_t server_name_length);

    # DLL_EXPORT void uws_remove_server_name(int ssl, uws_app_t *app, const char *hostname_pattern, size_t hostname_pattern_length);
    # DLL_EXPORT void uws_add_server_name(int ssl, uws_app_t *app, const char *hostname_pattern, size_t hostname_pattern_length);
    # DLL_EXPORT void uws_add_server_name_with_options(int ssl, uws_app_t *app, const char *hostname_pattern, size_t hostname_pattern_length, struct us_socket_context_options_t options);
    # DLL_EXPORT void uws_missing_server_name(int ssl, uws_app_t *app, uws_missing_server_handler handler, void *user_data);
    # DLL_EXPORT void uws_filter(int ssl, uws_app_t *app, uws_filter_handler handler, void *user_data);



# from socketify import App
from socketify import App, AppOptions, OpCode

# import os
import multiprocessing
import asyncio
import time
import mimetypes
mimetypes.init()


async def home(res, req):
    res.end("Home")

def ws_open(ws):
    print("Upgrated!")
    print(ws.send("Xablau!", OpCode.TEXT))

def ws_message(ws, message, opcode):
    print(message, opcode)

async def ws_upgrade(res, req, socket_context):
    key = req.get_header("sec-websocket-key")
    protocol = req.get_header("sec-websocket-protocol")
    extensions = req.get_header("sec-websocket-extensions")
    await asyncio.sleep(2)
    print("request upgrade!")
    res.upgrade(key, protocol, extensions, socket_context)
    
app = App()    
app.ws("/*", {
    'open': ws_open,
    'message': ws_message,
    'upgrade': ws_upgrade
})
app.get("/", home)
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % (config.port)))
app.run()

# def create_fork():
#     n = os.fork()
#     # n greater than 0 means parent process
#     if not n > 0:
#         run_app()

#openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -passout pass:1234 -keyout ./misc/key.pem -out ./misc/cert.pem 
# # fork limiting the cpu count - 1
# for i in range(1, multiprocessing.cpu_count()):
#     create_fork()

# run_app() # run app on the main process too :)
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