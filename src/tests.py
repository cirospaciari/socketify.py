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


# try_end
# get_full_url
# for_each_header
# https://github.com/uNetworking/uWebSockets.js/blob/master/examples/VideoStreamer.js
from socketify import App
# import os
import multiprocessing
import asyncio
import aiofiles
from aiofiles import os
import time
import mimetypes
mimetypes.init()

#need to fix get_data using sel._data etc
async def home(res, req):

    filename = "./file_example_MP3_5MG.mp3"
    
    if_modified_since = req.get_header('if-modified-since')
    range_header = req.get_header('range')
    bytes_range = None
    start = 0
    end = -1
    if range_header:
        bytes_range = range_header.replace("bytes=", '').split('-')
        start = int(bytes_range[0])
        if bytes_range[1]:
            end = int(bytes_range[1])
    try:
        exists = await os.path.exists(filename)
        if not exists:
            return res.write_status(404).end(b'Not Found')
        stats = await os.stat(filename)
        total_size = stats.st_size
        last_modified = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(stats.st_mtime))
        if if_modified_since == last_modified:
            res.write_status(304).end_without_body()
            return 
        res.write_header(b'Last-Modified', last_modified)

        (content_type, encoding) = mimetypes.guess_type(filename, strict=True)
        if content_type and encoding:
            res.write_header(b'Content-Type', '%s; %s' % (content_type, encoding))
        elif content_type:
            res.write_header(b'Content-Type', content_type)
        
        async with aiofiles.open(filename, "rb") as fd:
            if start > 0 or not end == -1:
                if end < 1 or end >= total_size:
                    end = total_size
                total_size = end - start
                await fd.seek(start)
                res.write_status(206)
            else:
                end = total_size
                res.write_status(200)
                
            #tells the browser that we support ranges
            res.write_header(b'Accept-Ranges', b'bytes')
            res.write_header(b'Content-Range', 'bytes %d-%d/%d' % (start, end, total_size))

            while not res.aborted:
                buffer = await fd.read(16384) #16kb chunks
                (ok, done) = await res.send_chunk(buffer, total_size)
                if not ok or done: #if cannot send probably aborted
                    break 
    except Exception as error:
        print(str(error))
        res.write_status(500).end("Internal Error")

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