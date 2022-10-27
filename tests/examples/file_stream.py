from socketify import App
import aiofiles
from aiofiles import os
import time
import mimetypes
from os import path

mimetypes.init()

async def home(res, req):
    #there is also a helper called static with an send_file method see static_files.py for examples of usage
    #here is an sample implementation, a more complete one is in static.send_file

    filename = "./public/media/flower.webm"
    #read headers before the first await
    if_modified_since = req.get_header('if-modified-since')

    try:
        exists = await os.path.exists(filename)
        #not found
        if not exists:
            return res.write_status(404).end(b'Not Found')

        #get size and last modified date
        stats = await os.stat(filename)
        total_size = stats.st_size
        last_modified = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(stats.st_mtime))
        
        #check if modified since is provided
        if if_modified_since == last_modified:
            res.write_status(304).end_without_body()
            return 
        #tells the broswer the last modified date
        res.write_header(b'Last-Modified', last_modified)

        #add content type
        (content_type, encoding) = mimetypes.guess_type(filename, strict=True)
        if content_type and encoding:
            res.write_header(b'Content-Type', '%s; %s' % (content_type, encoding))
        elif content_type:
            res.write_header(b'Content-Type', content_type)
        
        async with aiofiles.open(filename, "rb") as fd:
            res.write_status(200)
 
            pending_size = total_size
            #keep sending until abort or done
            while not res.aborted:
                chunk_size = 16384 #16kb chunks
                if chunk_size > pending_size:
                    chunk_size = pending_size
                buffer = await fd.read(chunk_size)
                pending_size = pending_size - chunk_size
                (ok, done) = await res.send_chunk(buffer, total_size)
                if not ok or done or pending_size <= 0: #if cannot send probably aborted
                    break
                

    except Exception as error:
        res.write_status(500).end("Internal Error")     

app = App()
app.get("/", home)
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()