import os
import time
import mimetypes
import inspect
from os import path

mimetypes.init()

# We have an version of this using aiofile and aiofiles
# This is an sync version without any dependencies is normally much faster in CPython and PyPy3
# In production we highly recommend to use CDN like CloudFlare or/and NGINX or similar for static files
# TODO: this must be reimplemented pure C++ to avoid GIL 
async def sendfile(res, req, filename):
    # read headers before the first await
    if_modified_since = req.get_header("if-modified-since")
    range_header = req.get_header("range")
    bytes_range = None
    start = 0
    end = -1
    # parse range header
    if range_header:
        bytes_range = range_header.replace("bytes=", "").split("-")
        start = int(bytes_range[0])
        if bytes_range[1]:
            end = int(bytes_range[1])
    try:
        exists = path.exists(filename)
        # not found
        if not exists:
            return res.cork(lambda res: res.write_status(404).end(b"Not Found"))

        # get size and last modified date
        stats = os.stat(filename)
        total_size = stats.st_size
        size = total_size
        last_modified = time.strftime(
            "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stats.st_mtime)
        )

        # check if modified since is provided
        if if_modified_since == last_modified:
            return res.cork(lambda res: res.write_status(304).end_without_body()) 

        # add content type
        (content_type, encoding) = mimetypes.guess_type(filename, strict=True)
        if content_type and encoding:
            content_type = "%s; %s" % (content_type, encoding)
        
        with open(filename, "rb") as fd:
            # check range and support it
            if start > 0 or not end == -1:
                if end < 0 or end >= size:
                    end = size - 1
                size = end - start + 1
                fd.seek(start)
                if start > total_size or size > total_size or size < 0 or start < 0:
                    if content_type:
                        return res.cork(lambda res: res.write_header(b"Content-Type", content_type).write_status(416).end_without_body())        
                    return res.cork(lambda res: res.write_status(416).end_without_body()) 
                status = 206
            else:
                end = size - 1
                status = 200

            def send_headers(res):
                res.write_status(status)
                # tells the broswer the last modified date
                res.write_header(b"Last-Modified", last_modified)

                # tells the browser that we support range
                if content_type:
                    res.write_header(b"Content-Type", content_type)
                res.write_header(b"Accept-Ranges", b"bytes")
                res.write_header(
                    b"Content-Range", "bytes %d-%d/%d" % (start, end, total_size)
                )
            res.cork(send_headers)
            pending_size = size
            # keep sending until abort or done
            while not res.aborted:
                chunk_size = 16384  # 16kb chunks
                if chunk_size > pending_size:
                    chunk_size = pending_size
                buffer = fd.read(chunk_size)
                pending_size = pending_size - chunk_size
                (ok, done) = await res.send_chunk(buffer, size)
                if not ok or done:  # if cannot send probably aborted
                    break

    except Exception as error:
        res.cork(lambda res: res.write_status(500).end("Internal Error"))


def in_directory(file, directory):
    # make both absolute
    directory = path.join(path.realpath(directory), "")
    file = path.realpath(file)
    # return true, if the common prefix of both is equal to directory
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return path.commonprefix([file, directory]) == directory


def static_route(app, route, directory):
    def route_handler(res, req):
        url = req.get_url()
        res.grab_aborted_handler()
        url = url[len(route)::]
        if url.endswith("/"):
            if url.startswith("/"):   
                url = url[1:-1]
            else:
                url = url[:-1]
        elif url.startswith("/"):
            url = url[1:]

        filename = path.join(path.realpath(directory), url)
        if not in_directory(filename, directory):
            res.write_status(404).end_without_body()
            return
        res.run_async(sendfile(res, req, filename))

    if route.endswith("/"):
        route = route[:-1]
    app.get("%s/*" % route, route_handler)


def middleware(*functions):
    # we use Optional data=None at the end so you can use and middleware inside a middleware
    async def middleware_route(res, req, data=None):
        some_async_as_run = False
        # cicle to all middlewares
        for function in functions:
            # detect if is coroutine or not
            if inspect.iscoroutinefunction(function):
                # in async query string, arguments and headers are only valid until the first await
                if not some_async_as_run:
                    # preserve queries, headers, parameters, url, full_url and method
                    req.preserve()
                    some_async_as_run = True
                data = await function(res, req, data)
            else:
                # call middlewares
                data = function(res, req, data)
            # stops if returns Falsy
            if not data:
                break
        return data

    return middleware_route


class MiddlewareRouter:
    def __init__(self, app, *middlewares):
        self.app = app
        self.middlewares = middlewares

    def get(self, path, handler):
        middies = list(self.middlewares)
        middies.append(handler)
        self.app.get(path, middleware(*middies))
        return self

    def post(self, path, handler):
        middies = list(self.middlewares)
        middies.append(handler)
        self.app.post(path, middleware(*middies))
        return self

    def options(self, path, handler):
        middies = list(self.middlewares)
        middies.append(handler)
        self.app.options(path, middleware(*middies))
        return self

    def delete(self, path, handler):
        middies = list(self.middlewares)
        middies.append(handler)
        self.app.delete(path, middleware(*middies))
        return self

    def patch(self, path, handler):
        middies = list(self.middlewares)
        middies.append(handler)
        self.app.patch(path, middleware(*middies))
        return self

    def put(self, path, handler):
        middies = list(self.middlewares)
        middies.append(handler)
        self.app.put(path, middleware(*middies))
        return self

    def head(self, path, handler):
        middies = list(self.middlewares)
        middies.append(handler)
        self.app.head(path, middleware(*middies))
        return self

    def connect(self, path, handler):
        middies = list(self.middlewares)
        middies.append(handler)
        self.app.connect(path, middleware(*middies))
        return self

    def trace(self, path, handler):
        middies = list(self.middlewares)
        middies.append(handler)
        self.app.trace(path, middleware(*middies))
        return self

    def any(self, path, handler):
        middies = list(self.middlewares)
        middies.append(handler)
        self.app.any(path, middleware(*middies))
        return self
