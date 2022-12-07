#include "uv.h"
#include "libsocketify.h"
#include <stdlib.h>
#include <stdio.h>
#include "libuwebsockets.cpp" //include symbols

extern "C"
{


static std::map<int, const char*> status_codes{
    { 100, "100 Continue" },
    { 101, "101 Switching Protocols"},
    { 102, "102 Processing" },
    { 103, "103 Early Hints"},
    { 200, "200 OK" },
    { 201, "201 Created"},
    { 202, "202 Accepted"},
    { 203, "203 Non-Authoritative Information"},
    { 204, "204 No Content"},
    { 205, "205 Reset Content"},
    { 206, "206 Partial Content"},
    { 207, "207 Multi-Status"},
    { 208, "208 Already Reported"},
    { 226, "226 IM Used (HTTP Delta encoding)"},
    { 300, "300 Multiple Choices"},
    { 301, "301 Moved Permanently"},
    { 302, "302 Found" },
    { 303, "303 See Other"},
    { 304, "304 Not Modified"},
    { 305, "305 Use Proxy Deprecated"},
    { 306, "306 unused" },
    { 307, "307 Temporary Redirect"},
    { 308, "308 Permanent Redirect"},
    { 400, "400 Bad Request"},
    { 401, "401 Unauthorized" },
    { 402, "402 Payment Required Experimental"},
    { 403, "403 Forbidden" },
    { 404, "404 Not Found"},
    { 405, "405 Method Not Allowed"},
    { 406, "406 Not Acceptable"},
    { 407, "407 Proxy Authentication Required"},
    { 408, "408 Request Timeout"},
    { 409, "409 Conflict" },
    { 410, "410 Gone"},
    { 411, "411 Length Required"},
    { 412, "412 Precondition Failed"},
    { 413, "413 Payload Too Large"},
    { 414, "414 URI Too Long"},
    { 415, "415 Unsupported Media Type"},
    { 416, "416 Range Not Satisfiable"},
    { 417, "417 Expectation Failed"},
    { 418, "418 I'm a teapot"},
    { 421, "421 Misdirected Request"},
    { 422, "422 Unprocessable Entity"},
    { 423, "423 Locked" },
    { 424, "424 Failed Dependency"},
    { 425, "425 Too Early Experimental"},
    { 426, "426 Upgrade Required"},
    { 428, "428 Precondition Required"},
    { 429, "429 Too Many Requests"},
    { 431, "431 Request Header Fields Too Large"},
    { 451, "451 Unavailable For Legal Reasons"},
    { 500, "500 Internal Server Error"},
    { 501, "501 Not Implemented"},
    { 502, "502 Bad Gateway"},
    { 503, "503 Service Unavailable"},
    { 504, "504 Gateway Timeout"},
    { 505, "505 HTTP Version Not Supported"},
    { 506, "506 Variant Also Negotiates"},
    { 507, "507 Insufficient Storage"},
    { 508, "508 Loop Detected"},
    { 510, "510 Not Extended"},
    { 511, "511 Network Authentication Required"}
};

bool socketify_res_write_int_status(int ssl, uws_res_t* res, int code) {
    if (code == 200) {
        uws_res_write_status(ssl, res, "200 OK", 6);
        return true; //default
    }
    std::map<int,const char*>::iterator it = status_codes.find(code);
    if(it != status_codes.end())
    {
        //element found;
       const char* status = it->second;
       uws_res_write_status(ssl, res, status, strlen(status));
       return true;   
    }
    return false;
}



void socketify_res_write_headers(int ssl, uws_res_t* res, socketify_header* headers) {
    while (headers != NULL)
    {
        uws_res_write_header(ssl, res, headers->name, headers->name_size, headers->value, headers->value_size);
    }
}

bool socketify_res_write_int_status_with_headers(int ssl, uws_res_t* res, int code, socketify_header* headers) {
    if(socketify_res_write_int_status(ssl, res, code)){
        socketify_res_write_headers(ssl, res, headers);
        return true;
    }
    return false;
}
void socketify_destroy_headers(socketify_header* headers){

    socketify_header* current = headers;
    while(current != NULL){
        socketify_header* next = (socketify_header*)current->next;
        free(current);
        current = next;
    }
}

socketify_asgi_data socketify_asgi_request(int ssl, uws_req_t *req, uws_res_t *res){

    socketify_asgi_data result;

    const char *full_url = NULL;
    const char *query_string = NULL;
    const char *url = NULL;
    const char *method = NULL;

    size_t full_url_size = uws_req_get_full_url(req, &full_url);
    size_t url_size = uws_req_get_url(req, &url);
    size_t method_size = uws_req_get_case_sensitive_method(req, &method);

    query_string = full_url + url_size;
    size_t query_string_size = full_url_size - url_size;

    const char *remote_address = NULL;
    size_t remote_address_size = uws_res_get_remote_address_as_text(ssl, res, &remote_address);

    result.full_url = full_url;
    result.url = url;
    result.query_string = query_string;
    result.method = method;
    result.remote_address = remote_address;
    result.full_url_size = full_url_size;
    result.url_size = url_size;
    result.query_string_size = query_string_size;
    result.method_size = method_size;
    result.remote_address_size = remote_address_size;
    result.has_content = false;
    uWS::HttpRequest *uwsReq = (uWS::HttpRequest *)req;
    result.header_list = NULL;
    socketify_header* last = NULL;
    for (auto header : *uwsReq)
    {
        socketify_header* current = (socketify_header*)malloc(sizeof(socketify_header));
        auto name = header.first;
        auto value = header.second;
        
        current->name = name.data();
        current->name_size = name.length();
        
        if(name.compare("content-length") == 0 || name.compare("transfer-encoding") == 0){
            result.has_content = true;
        }

        current->value = header.second.data();
        current->value_size = header.second.length();
        current->next = NULL;
        if(last == NULL){
            result.header_list = current;
            last = current;
        }else{
            last->next = current;
            last = current;
        }
    }
    return result;
    
}

socketify_asgi_ws_data socketify_asgi_ws_request(int ssl, uws_req_t *req, uws_res_t *res){

    socketify_asgi_ws_data result;

    const char *full_url = NULL;
    const char *query_string = NULL;
    const char *url = NULL;
    const char *method = NULL;

    size_t full_url_size = uws_req_get_full_url(req, &full_url);
    size_t url_size = uws_req_get_url(req, &url);
    size_t method_size = uws_req_get_case_sensitive_method(req, &method);

    query_string = full_url + url_size;
    size_t query_string_size = full_url_size - url_size;

    const char *remote_address = NULL;
    size_t remote_address_size = uws_res_get_remote_address_as_text(ssl, res, &remote_address);

    result.full_url = full_url;
    result.url = url;
    result.query_string = query_string;
    result.method = method;
    result.remote_address = remote_address;
    result.full_url_size = full_url_size;
    result.url_size = url_size;
    result.query_string_size = query_string_size;
    result.method_size = method_size;
    result.remote_address_size = remote_address_size;

    uWS::HttpRequest *uwsReq = (uWS::HttpRequest *)req;
    result.header_list = NULL;
    socketify_header* last = NULL;

    const char *protocol = NULL;
    const char *extensions = NULL;
    const char *key = NULL;
    size_t protocol_size = 0;
    size_t extensions_size = 0;
    size_t key_size = 0;
    
    for (auto header : *uwsReq)
    {
        auto name = header.first;
        auto value = header.second;
        const char* value_data = value.data();
        size_t value_size = value.length();
        
        if (name.compare("sec-websocket-key") == 0){
            key = value_data;
            key_size = value_size;
        }else if (name.compare("sec-websocket-protocol") == 0){
            protocol = value_data;
            protocol_size = value_size;
            continue;//exclude protocol
        }else if (name.compare("sec-websocket-extensions") == 0){
            extensions = value_data;
            extensions_size = value_size;
        }

        socketify_header* current = (socketify_header*)malloc(sizeof(socketify_header));
        current->name = name.data();
        current->name_size = name.length();
        current->value = value_data;
        current->value_size = value_size;


        current->next = NULL;
        if(last == NULL){
            result.header_list = current;
            last = current;
        }else{
            last->next = current;
            last = current;
        }
    }
    result.protocol = protocol;
    result.key = key;
    result.extensions = extensions;
    result.protocol_size = protocol_size;
    result.key_size = key_size;
    result.extensions_size = extensions_size;
    return result;
    
}

void socketify_asgi_http_handler(uws_res_t *response, uws_req_t *request, void *user_data){
    socksocketify_asgi_app_info* info = ((socksocketify_asgi_app_info*)user_data);
    socketify_asgi_data data = socketify_asgi_request(info->ssl, request, response);
    bool* aborted = (bool*)malloc(sizeof(aborted));
    *aborted = false;
    uws_res_on_aborted(info->ssl, response, [](uws_res_t *res, void *opcional_data){
        bool* aborted = (bool*)opcional_data;
        *aborted = true;
    }, aborted);
    info->handler(info->ssl, response, data, info->user_data, aborted);
    socketify_destroy_headers(data.header_list);
}



void socketify_res_cork_write(int ssl, uws_res_t *res, const char* data, size_t length){
    if (ssl)
    {
        uWS::HttpResponse<true> *uwsRes = (uWS::HttpResponse<true> *)res;
        uwsRes->cork([=](){
             uwsRes->write(std::string_view(data, length));
        });
    }
    else
    {
        uWS::HttpResponse<false> *uwsRes = (uWS::HttpResponse<false> *)res;
        uwsRes->cork([=](){
             uwsRes->write(std::string_view(data, length));
        });
    }
}

void socketify_res_cork_end(int ssl, uws_res_t *res, const char* data, size_t length, bool close_connection){
    if (ssl)
    {
        uWS::HttpResponse<true> *uwsRes = (uWS::HttpResponse<true> *)res;
        uwsRes->cork([=](){
             uwsRes->end(std::string_view(data, length), close_connection);
        });
    }
    else
    {
        uWS::HttpResponse<false> *uwsRes = (uWS::HttpResponse<false> *)res;
        uwsRes->cork([=](){
             uwsRes->end(std::string_view(data, length), close_connection);
        });
    }
}
void socketify_ws_cork_send(int ssl, uws_websocket_t *ws, const char* data, size_t length, uws_opcode_t opcode){
    if (ssl)
    {
        uWS::WebSocket<true, true, void *> *uws = (uWS::WebSocket<true, true, void *> *)ws;
        uws->cork([&](){ 
            uws->send(std::string_view(data, length), (uWS::OpCode)(unsigned char) opcode);
        });
    }
    else
    {
        uWS::WebSocket<false, true, void *> *uws = (uWS::WebSocket<false, true, void *> *)ws;
        uws->cork([&](){ 
            uws->send(std::string_view(data, length), (uWS::OpCode)(unsigned char) opcode);
        });
    }

}

void socketify_ws_cork_send_with_options(int ssl, uws_websocket_t *ws, const char* data, size_t length, uws_opcode_t opcode, bool compress, bool fin){
    if (ssl)
    {
        uWS::WebSocket<true, true, void *> *uws = (uWS::WebSocket<true, true, void *> *)ws;
        uws->cork([&](){ 
            uws->send(std::string_view(data, length), (uWS::OpCode)(unsigned char) opcode, compress, fin);
        });
    }
    else
    {
        uWS::WebSocket<false, true, void *> *uws = (uWS::WebSocket<false, true, void *> *)ws;
        uws->cork([&](){ 
            uws->send(std::string_view(data, length), (uWS::OpCode)(unsigned char) opcode, compress, fin);
        });
    }
}


socksocketify_asgi_ws_app_info* socketify_add_asgi_ws_handler(int ssl, uws_app_t* app, uws_socket_behavior_t behavior, socketify_asgi_ws_method_handler handler, void* user_data){
    socksocketify_asgi_ws_app_info* info = (socksocketify_asgi_ws_app_info*)malloc(sizeof(socksocketify_asgi_ws_app_info));
    info->ssl = ssl;
    info->app = app;
    info->handler = handler;
    info->user_data = user_data;
    info->behavior = behavior;

    const char* pattern = "/*";
    uws_socket_behavior_t ws_behavior;
    memcpy(&ws_behavior, &behavior, sizeof(behavior));
    
    ws_behavior.upgrade = [](uws_res_t *response, uws_req_t *request, uws_socket_context_t *context, void* user_data){
        socksocketify_asgi_ws_app_info* info = ((socksocketify_asgi_ws_app_info*)user_data);
        socketify_asgi_ws_data data = socketify_asgi_ws_request(info->ssl, request, response);
        bool* aborted = (bool*)malloc(sizeof(aborted));
        *aborted = false;
        uws_res_on_aborted(info->ssl, response, [](uws_res_t *res, void *opcional_data){
            bool* aborted = (bool*)opcional_data;
            *aborted = true;
        }, aborted);
        info->handler(info->ssl, response, data, context, info->user_data, aborted);
        socketify_destroy_headers(data.header_list);
    };
    ws_behavior.open = [](uws_websocket_t *ws, void* user_data){
        socksocketify_asgi_ws_app_info* info = ((socksocketify_asgi_ws_app_info*)user_data);
        auto socket_data = uws_ws_get_user_data(info->ssl, ws);
        info->behavior.open(ws, socket_data);
    };
    ws_behavior.message = [](uws_websocket_t* ws, const char* message, size_t length, uws_opcode_t opcode, void* user_data){
        socksocketify_asgi_ws_app_info* info = ((socksocketify_asgi_ws_app_info*)user_data);
        auto socket_data = uws_ws_get_user_data(info->ssl, ws);
        info->behavior.message(ws, message, length, opcode, socket_data);
    };

    ws_behavior.close = [](uws_websocket_t* ws, int code, const char* message, size_t length, void* user_data){
        socksocketify_asgi_ws_app_info* info = ((socksocketify_asgi_ws_app_info*)user_data);
        auto socket_data = uws_ws_get_user_data(info->ssl, ws);
        info->behavior.close(ws,code,  message, length, socket_data);
    };
    
    uws_ws(ssl, app, pattern, ws_behavior, info);
    return info;
}

socksocketify_asgi_app_info* socketify_add_asgi_http_handler(int ssl, uws_app_t* app, socketify_asgi_method_handler handler, void* user_data){
    socksocketify_asgi_app_info* info = (socksocketify_asgi_app_info*)malloc(sizeof(socksocketify_asgi_app_info));
    info->ssl = ssl;
    info->app = app;
    info->handler = handler;
    info->user_data = user_data;

    const char* pattern = "/*";
    uws_app_any(ssl, app, pattern, socketify_asgi_http_handler, info);
    return info;
}

void socketify_destroy_asgi_app_info(socksocketify_asgi_app_info* app){
    free(app);
}
void socketify_destroy_asgi_ws_app_info(socksocketify_asgi_ws_app_info* app){
    free(app);
}

void socketify_generic_prepare_callback(uv_prepare_t *prepare){
    socketify_loop* loop = (socketify_loop*)uv_handle_get_data((uv_handle_t*)prepare);
    loop->on_prepare_handler(loop->on_prepare_data);
}

void socketify_generic_timer_callback(uv_timer_t *timer){
    socketify_timer* loop_data = (socketify_timer*)uv_handle_get_data((uv_handle_t*)timer);
    loop_data->handler(loop_data->user_data);
}

void socketify_generic_check_callback(uv_check_t *timer){
    socketify_timer* loop_data = (socketify_timer*)uv_handle_get_data((uv_handle_t*)timer);
    loop_data->handler(loop_data->user_data);
}


void* socketify_get_native_loop(socketify_loop* loop){
    return loop->uv_loop;
}

socketify_loop * socketify_create_loop(){
    socketify_loop* loop = (socketify_loop*)malloc(sizeof(uv_prepare_t));
    loop->uv_loop = NULL;
    loop->on_prepare_handler = NULL;
    loop->uv_prepare_ptr = NULL;

    uv_loop_t* uv_loop = (uv_loop_t*)malloc(sizeof(uv_loop_t));
    if(uv_loop_init(uv_loop)){
        free(uv_loop);
        return loop;
    }
    loop->uv_loop = uv_loop;
    return loop;
}

bool socketify_constructor_failed(socketify_loop* loop){
    return loop->uv_loop == NULL;
}

bool socketify_on_prepare(socketify_loop* loop, socketify_prepare_handler handler, void* user_data){
    if (loop->uv_prepare_ptr != NULL) return false;
    if(handler == NULL) return false;
    uv_prepare_t* prepare = (uv_prepare_t*)malloc(sizeof(uv_prepare_t));
    if(uv_prepare_init((uv_loop_t*)loop->uv_loop, prepare)){
        free(prepare);
        return false;
    }
    
    loop->on_prepare_handler = handler;
    loop->on_prepare_data = user_data;
    loop->uv_prepare_ptr = prepare;
    uv_handle_set_data((uv_handle_t*)prepare, loop);
    uv_prepare_start(prepare, socketify_generic_prepare_callback);

    return true;
}

bool socketify_prepare_unbind(socketify_loop* loop){
    if(loop->uv_prepare_ptr == NULL) return false;
    uv_prepare_stop((uv_prepare_t *)loop->uv_prepare_ptr);

    free(loop->uv_prepare_ptr);
    loop->uv_prepare_ptr = NULL;
    return true;
}

int socketify_loop_run(socketify_loop* loop, socketify_run_mode mode){
    return uv_run((uv_loop_t*)loop->uv_loop, (uv_run_mode)mode);
}

void socketify_loop_stop(socketify_loop* loop){
     if(uv_loop_alive((uv_loop_t*)loop->uv_loop)){
        uv_stop((uv_loop_t*)loop->uv_loop);
    }
}

void socketify_destroy_loop(socketify_loop* loop){
    socketify_loop_stop(loop);

    uv_loop_close((uv_loop_t*)loop->uv_loop);
    free(loop->uv_loop);
    if(loop->uv_prepare_ptr){
        free(loop->uv_prepare_ptr);
    }
    free(loop);
}

socketify_timer* socketify_create_timer(socketify_loop* loop, uint64_t timeout, uint64_t repeat, socketify_timer_handler handler, void* user_data){
       
    uv_timer_t* uv_timer = (uv_timer_t* ) malloc(sizeof(uv_timer_t));
    
    if(uv_timer_init((uv_loop_t*)loop->uv_loop, uv_timer)){
         free(uv_timer);
         return NULL;
    }

    socketify_timer* timer = (socketify_timer*)malloc(sizeof(socketify_timer));
    timer->uv_timer_ptr = uv_timer;
    timer->user_data = user_data;
    timer->handler = handler;

    uv_handle_set_data((uv_handle_t*)uv_timer, timer);
    uv_timer_start(uv_timer, socketify_generic_timer_callback, timeout, repeat); 

    return timer;
}

void socketify_timer_set_repeat(socketify_timer* timer, uint64_t repeat){
    uv_timer_set_repeat((uv_timer_t *) timer->uv_timer_ptr, repeat);
}


//stops and destroy timer info
void socketify_timer_destroy(socketify_timer* timer){
    uv_timer_stop((uv_timer_t *)timer->uv_timer_ptr);
    free(timer->uv_timer_ptr);
    free(timer);
}



socketify_timer* socketify_create_check(socketify_loop* loop, socketify_timer_handler handler, void* user_data){
       
    uv_check_t* uv_timer = (uv_check_t*)malloc(sizeof(uv_check_t));
    if(uv_check_init((uv_loop_t*)loop->uv_loop, uv_timer)){
         free(uv_timer);
         return NULL;
    }

    socketify_timer* timer = (socketify_timer*)malloc(sizeof(socketify_timer));
    timer->uv_timer_ptr = uv_timer;
    timer->user_data = user_data;
    timer->handler = handler;

    uv_handle_set_data((uv_handle_t*)uv_timer, timer);
    uv_check_start(uv_timer, socketify_generic_check_callback); 

    return timer;
}

//stops and destroy timer info
void socketify_check_destroy(socketify_timer* timer){
    uv_check_stop((uv_check_t *)timer->uv_timer_ptr);
    free(timer->uv_timer_ptr);
    free(timer);
}
}