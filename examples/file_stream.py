from socketify import App
import aiofiles
import time
import mimetypes
import os
from os import path

mimetypes.init()

async def home(res, req):
    #this is just an implementation example see static_files.py example for use of sendfile and app.static usage
    #there is an static_aiofile.py helper and static.aiofiles helper using async implementation of this 
    #asyncio with IO is really slow so, we will implement "aiofile" using libuv inside socketify in future

    filename = "./public/media/flower.webm"
    #read headers before the first await
    if_modified_since = req.get_header('if-modified-since')
    range_header = req.get_header('range')
    bytes_range = None
    start = 0
    end = -1
    #parse range header
    if range_header:
        bytes_range = range_header.replace("bytes=", '').split('-')
        start = int(bytes_range[0])
        if bytes_range[1]:
            end = int(bytes_range[1])
    try:
        exists = path.exists(filename)
        #not found
        if not exists:
            return res.write_status(404).end(b'Not Found')

        #get size and last modified date
        stats = os.stat(filename)
        total_size = stats.st_size
        size = total_size
        last_modified = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(stats.st_mtime))
        
        #check if modified since is provided
        if if_modified_since == last_modified:
            return res.write_status(304).end_without_body()
        #tells the broswer the last modified date
        res.write_header(b'Last-Modified', last_modified)

        #add content type
        (content_type, encoding) = mimetypes.guess_type(filename, strict=True)
        if content_type and encoding:
            res.write_header(b'Content-Type', '%s; %s' % (content_type, encoding))
        elif content_type:
            res.write_header(b'Content-Type', content_type)
        
        with open(filename, "rb") as fd:
            #check range and support it
            if start > 0 or not end == -1:
                if end < 0 or end >= size:
                    end = size - 1
                size = end - start + 1
                fd.seek(start)
                if start > total_size or size > total_size or size < 0 or start < 0:
                    return res.write_status(416).end_without_body()
                res.write_status(206)
            else:
                end = size - 1
                res.write_status(200)
            
            #tells the browser that we support range 
            res.write_header(b'Accept-Ranges', b'bytes') 
            res.write_header(b'Content-Range', 'bytes %d-%d/%d' % (start, end, total_size))
            pending_size = size
            #keep sending until abort or done
            while not res.aborted:
                chunk_size = 16384 #16kb chunks
                if chunk_size > pending_size:
                    chunk_size = pending_size
                buffer = fd.read(chunk_size)
                pending_size = pending_size - chunk_size
                (ok, done) = await res.send_chunk(buffer, size)
                if not ok or done: #if cannot send probably aborted
                    break

    except Exception as error:
        res.write_status(500).end("Internal Error")   

app = App()
app.get("/", home)
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()