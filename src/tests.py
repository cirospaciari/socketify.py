# https://github.com/Tinche/aiofiles
# https://github.com/uNetworking/uWebSockets/issues/1426

# import os.path

# DLL_EXPORT typedef void (*uws_listen_domain_handler)(struct us_listen_socket_t *listen_socket, const char* domain, size_t domain_length, int options, void *user_data);    
# DLL_EXPORT typedef void (*uws_filter_handler)(uws_res_t *response, int, void *user_data);

# DLL_EXPORT void uws_app_listen_domain(int ssl, uws_app_t *app, const char *domain,size_t server_name_length,_listen_domain_handler handler, void *user_data);
# DLL_EXPORT void uws_app_listen_domain_with_options(int ssl, uws_app_t *app, const char *domain,size_t servere_length, int options, uws_listen_domain_handler handler, void *user_data);
# DLL_EXPORT void uws_app_domain(int ssl, uws_app_t *app, const char* server_name, size_t server_name_length);
# DLL_EXPORT void uws_filter(int ssl, uws_app_t *app, uws_filter_handler handler, void *user_data);


from socketify import App, AppOptions, OpCode, CompressOptions
import asyncio

def ws_open(ws):
    print('A WebSocket got connected!')
    ws.send("Hello World!", OpCode.TEXT)

def ws_message(ws, message, opcode):
    print(message, opcode)
    #Ok is false if backpressure was built up, wait for drain
    ok = ws.send(message, opcode)

async def ws_upgrade(res, req, socket_context):
    key = req.get_header("sec-websocket-key")
    protocol = req.get_header("sec-websocket-protocol")
    extensions = req.get_header("sec-websocket-extensions")
    await asyncio.sleep(2)
    res.upgrade(key, protocol, extensions, socket_context)
    
app = App()    
app.ws("/*", {
    'compression': CompressOptions.SHARED_COMPRESSOR,
    'max_payload_length': 16 * 1024 * 1024,
    'idle_timeout': 12,
    'open': ws_open,
    'message': ws_message,
    'upgrade': ws_upgrade
})
app.any("/", lambda res,req: res.end("Nothing to see here!"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % (config.port)))
app.run()