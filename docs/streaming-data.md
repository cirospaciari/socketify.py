# Streaming data
You should never call res.end(huge buffer). res.end guarantees sending so backpressure will probably spike. Instead you should use res.try_end to stream huge data part by part. Use in combination with res.on_writable and res.on_aborted callbacks.
For simplicity, you can use `res.send_chunk`, this will return an Future and use `res.on_writable` and `res.on_aborted` for you.

Using send_chunk:

```python
async def home(res, req):
    res.write_header("Content-Type", "audio/mpeg")
   
    filename = "./file_example_MP3_5MG.mp3"
    total = os.stat(filename).st_size
    
    async with aiofiles.open(filename, "rb") as fd:
        while not res.aborted:
            buffer = await fd.read(16384)  #16kb buffer
            (ok, done) = await res.send_chunk(buffer, total)
            if not ok or done: #if cannot send probably aborted
                break 
```

If you want to understand `res.send_chunk`, check out the implementation:
```python
def send_chunk(self, buffer, total_size):
        self._chunkFuture = self.loop.create_future()
        self._lastChunkOffset = 0

        def is_aborted(self):
            self.aborted = True
            try:
                if not self._chunkFuture.done():
                    self._chunkFuture.set_result(
                        (False, True)
                    )  # if aborted set to done True and ok False
            except:
                pass

        def on_writeble(self, offset):
            # Here the timeout is off, we can spend as much time before calling try_end we want to
            (ok, done) = self.try_end(
                buffer[offset - self._lastChunkOffset : :], total_size
            )
            if ok:
                self._chunkFuture.set_result((ok, done))
            return ok

        self.on_writable(on_writeble)
        self.on_aborted(is_aborted)

        if self.aborted:
            self._chunkFuture.set_result(
                (False, True)
            )  # if aborted set to done True and ok False
            return self._chunkFuture

        (ok, done) = self.try_end(buffer, total_size)
        if ok:
            self._chunkFuture.set_result((ok, done))
            return self._chunkFuture
        # failed to send chunk
        self._lastChunkOffset = self.get_write_offset()

        return self._chunkFuture
```

### Next [Send File and Static Files](static-files.md)